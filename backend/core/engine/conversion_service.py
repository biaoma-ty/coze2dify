from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import yaml
from sqlalchemy.orm import Session

from config import settings
from core.coze.api_client import CozeApiClient
from core.coze.db_reader import CozeDbReader
from core.dify.db_writer import DifyDbWriter
from core.dify.models import DifyDSL
from core.security.redaction import build_database_ref, sanitize_exception
from db.models import MigrationTask

from .converter import ConversionEngine


class ConversionService:
    """Persist conversion artifacts and bridge source/destination integrations."""

    def __init__(self, engine: ConversionEngine | None = None) -> None:
        self.engine = engine or ConversionEngine()

    def convert_uploaded_file(self, db: Session, content: bytes, filename: str | None = None) -> dict[str, Any]:
        fmt = "yaml" if filename and filename.endswith((".yaml", ".yml")) else "json"
        ir_workflow = self.engine.coze_parser.parse_file(content, fmt)
        source_workflow_id = ir_workflow.id or (filename or "")
        source_workflow_name = ir_workflow.name or (filename or "Uploaded workflow")
        return self._store_conversion(
            db=db,
            ir_workflow=ir_workflow,
            source_type="upload",
            source_workflow_id=source_workflow_id,
            source_workflow_name=source_workflow_name,
        )

    async def convert_from_api(
        self,
        db: Session,
        *,
        access_token: str,
        workflow_id: str,
        api_base: str | None = None,
    ) -> dict[str, Any]:
        client = CozeApiClient(access_token=access_token, base_url=api_base)
        payload = await client.fetch_workflow(workflow_id)
        canvas = self._extract_canvas(payload)
        ir_workflow = self.engine.coze_parser.parse_dict(canvas)
        return self._store_conversion(
            db=db,
            ir_workflow=ir_workflow,
            source_type="api",
            source_workflow_id=workflow_id,
            source_workflow_name=ir_workflow.name or workflow_id,
        )

    def convert_from_db(self, db: Session, *, db_url: str, workflow_id: str) -> dict[str, Any]:
        reader = CozeDbReader(db_url)
        payload = reader.read_workflow(workflow_id)
        if payload is None:
            raise LookupError(f"Workflow {workflow_id} not found in Coze database")

        canvas = self._extract_canvas(payload)
        ir_workflow = self.engine.coze_parser.parse_dict(canvas)
        source_workflow_name = ""
        if isinstance(payload, dict):
            source_workflow_name = str(payload.get("name") or "")

        return self._store_conversion(
            db=db,
            ir_workflow=ir_workflow,
            source_type="database",
            source_workflow_id=workflow_id,
            source_workflow_name=source_workflow_name or ir_workflow.name or workflow_id,
        )

    def get_conversion(self, db: Session, conversion_id: str) -> dict[str, Any]:
        task = self._get_task(db, conversion_id)
        snapshot = dict(task.ir_snapshot or {})
        dsl_payload = snapshot.get("dify_dsl")
        if dsl_payload is None and task.dify_dsl:
            dsl_payload = yaml.safe_load(task.dify_dsl)

        return {
            "conversion_id": str(task.id),
            "status": task.status,
            "source_type": task.source_type,
            "source_workflow_id": task.source_workflow_id,
            "source_workflow_name": task.source_workflow_name,
            "dsl": dsl_payload or {},
            "source_graph": self._build_source_graph(snapshot),
            "target_graph": self._build_target_graph(dsl_payload),
            "report": task.report or {},
            "write_result": self._serialize_write_result(snapshot.get("write_result")),
            "audit": self._serialize_audit(snapshot.get("audit"), task),
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    def list_conversions(self, db: Session, *, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        query = db.query(MigrationTask).filter(MigrationTask.sync_config_id.is_(None))
        total = query.count()
        tasks = (
            query.order_by(MigrationTask.created_at.desc(), MigrationTask.id.desc()).offset(offset).limit(limit).all()
        )
        return {
            "items": [self._serialize_history_item(task) for task in tasks],
            "total": total,
        }

    def get_yaml(self, db: Session, conversion_id: str) -> str:
        task = self._get_task(db, conversion_id)
        if not task.dify_dsl:
            raise LookupError(f"Conversion {conversion_id} has no DSL artifact")
        return task.dify_dsl

    def write_to_dify(
        self,
        db: Session,
        conversion_id: str,
        *,
        db_url: str | None = None,
        app_id: str | None = None,
    ) -> dict[str, Any]:
        task = self._get_task(db, conversion_id)
        target_db_url = db_url or settings.dify_database_url
        if not target_db_url:
            raise ValueError("Dify database URL is required")
        report = task.report or {}
        if not bool(report.get("supported", True)):
            blocking_issues = report.get("blocking_issues") or []
            detail = blocking_issues[0] if blocking_issues else "This workflow is outside the strict supported subset."
            raise ValueError(detail)

        snapshot = dict(task.ir_snapshot or {})
        dsl_payload = snapshot.get("dify_dsl")
        if dsl_payload is None:
            if not task.dify_dsl:
                raise LookupError(f"Conversion {conversion_id} has no DSL artifact")
            dsl_payload = yaml.safe_load(task.dify_dsl)

        dify_dsl = DifyDSL.model_validate(dsl_payload)
        writer = DifyDbWriter(target_db_url)
        write_started_at = datetime.now(timezone.utc)
        audit = self._serialize_audit(snapshot.get("audit"), task)

        try:
            if app_id:
                writer.update_workflow(app_id, dify_dsl)
                mode = "update"
                target_app_id = app_id
            else:
                target_app_id = writer.write_workflow(dify_dsl)
                mode = "create"
        except Exception as exc:  # noqa: BLE001 - persist sanitized write failure details
            sanitized_error = sanitize_exception(exc, db_urls=[target_db_url])
            write_result = self._build_write_result(
                mode="update" if app_id else "create",
                app_id=app_id,
                target_db_url=target_db_url,
                written_at=write_started_at,
                status="failed",
                error=sanitized_error,
                requested_app_id=app_id,
            )
            audit["last_write"] = write_result
            snapshot["audit"] = audit
            snapshot["write_result"] = write_result
            task.ir_snapshot = snapshot
            task.error_message = sanitized_error
            task.status = "write_failed"
            task.completed_at = write_started_at.replace(tzinfo=None)
            db.add(task)
            db.commit()
            db.refresh(task)
            raise RuntimeError(sanitized_error) from exc

        write_result = self._build_write_result(
            mode=mode,
            app_id=target_app_id,
            target_db_url=target_db_url,
            written_at=write_started_at,
            status="succeeded",
            requested_app_id=app_id,
        )
        audit["last_write"] = write_result
        snapshot["audit"] = audit
        snapshot["write_result"] = write_result
        task.ir_snapshot = snapshot
        task.error_message = None
        task.status = "updated" if mode == "update" else "written"
        task.completed_at = write_started_at.replace(tzinfo=None)
        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "conversion_id": str(task.id),
            "app_id": target_app_id,
            "mode": mode,
            "status": task.status,
            "write_result": write_result,
        }

    def _store_conversion(
        self,
        *,
        db: Session,
        ir_workflow: Any,
        source_type: str,
        source_workflow_id: str,
        source_workflow_name: str,
    ) -> dict[str, Any]:
        dify_dsl, report = self.engine.convert_from_ir(ir_workflow)
        snapshot = {
            "ir_workflow": ir_workflow.model_dump(mode="json"),
            "dify_dsl": dify_dsl.model_dump(mode="json") if dify_dsl else None,
            "write_result": None,
            "audit": {
                "source": {
                    "type": source_type,
                    "workflow_id": source_workflow_id,
                    "workflow_name": source_workflow_name,
                },
                "last_write": None,
            },
        }
        yaml_output = self.engine.dify_generator.to_yaml(dify_dsl) if dify_dsl else None
        task = MigrationTask(
            source_type=source_type,
            source_workflow_id=source_workflow_id,
            source_workflow_name=source_workflow_name,
            status="converted" if report.supported else "blocked",
            ir_snapshot=snapshot,
            dify_dsl=yaml_output,
            report=report.model_dump(mode="json"),
            error_message=report.blocking_issues[0] if report.blocking_issues else None,
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return self.get_conversion(db, str(task.id))

    @staticmethod
    def _get_task(db: Session, conversion_id: str) -> MigrationTask:
        try:
            task_id = int(conversion_id)
        except ValueError as exc:
            raise LookupError(f"Conversion {conversion_id} not found") from exc

        task = db.get(MigrationTask, task_id)
        if task is None:
            raise LookupError(f"Conversion {conversion_id} not found")
        return task

    @classmethod
    def _serialize_history_item(cls, task: MigrationTask) -> dict[str, Any]:
        snapshot = task.ir_snapshot or {}
        write_result = snapshot.get("write_result") if isinstance(snapshot, dict) else None
        if not isinstance(write_result, dict):
            write_result = None

        return {
            "conversion_id": str(task.id),
            "status": task.status,
            "source_type": task.source_type,
            "source_workflow_id": task.source_workflow_id,
            "source_workflow_name": task.source_workflow_name,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "write_result": cls._serialize_write_result(write_result),
            "audit": cls._serialize_audit(snapshot.get("audit"), task),
            "error_message": task.error_message,
            "report_summary": cls._build_report_summary(task.report),
        }

    @classmethod
    def _build_source_graph(cls, snapshot: dict[str, Any]) -> dict[str, Any] | None:
        ir_workflow = snapshot.get("ir_workflow")
        if not isinstance(ir_workflow, dict):
            return None

        nodes, child_edge_count = cls._flatten_ir_nodes(ir_workflow.get("nodes"))
        top_level_edges = ir_workflow.get("edges")
        edge_count = child_edge_count
        if isinstance(top_level_edges, list):
            edge_count += sum(1 for edge in top_level_edges if isinstance(edge, dict))

        return {
            "node_count": len(nodes),
            "edge_count": edge_count,
            "nodes": nodes,
        }

    @staticmethod
    def _build_target_graph(dsl_payload: Any) -> dict[str, Any] | None:
        if not isinstance(dsl_payload, dict):
            return None

        workflow = dsl_payload.get("workflow")
        if not isinstance(workflow, dict):
            return None

        graph = workflow.get("graph")
        if not isinstance(graph, dict):
            return None

        nodes_payload = graph.get("nodes")
        nodes: list[dict[str, Any]] = []
        if isinstance(nodes_payload, list):
            for node in nodes_payload:
                if not isinstance(node, dict):
                    continue

                data = node.get("data")
                if not isinstance(data, dict):
                    data = {}

                nodes.append(
                    {
                        "id": str(node.get("id") or ""),
                        "type": str(data.get("type") or node.get("type") or ""),
                        "title": str(data.get("title") or node.get("id") or ""),
                        "parent_id": str(node.get("parentId")) if node.get("parentId") else None,
                    }
                )

        edge_count = 0
        edges_payload = graph.get("edges")
        if isinstance(edges_payload, list):
            edge_count = sum(1 for edge in edges_payload if isinstance(edge, dict))

        return {
            "node_count": len(nodes),
            "edge_count": edge_count,
            "nodes": nodes,
        }

    @classmethod
    def _flatten_ir_nodes(
        cls,
        nodes_payload: Any,
        *,
        parent_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        if not isinstance(nodes_payload, list):
            return [], 0

        nodes: list[dict[str, Any]] = []
        edge_count = 0
        for node in nodes_payload:
            if not isinstance(node, dict):
                continue

            node_id = str(node.get("id") or "")
            nodes.append(
                {
                    "id": node_id,
                    "type": str(node.get("node_type") or node.get("type") or ""),
                    "title": str(node.get("title") or node_id or ""),
                    "parent_id": parent_id,
                }
            )

            child_edges = node.get("child_edges")
            if isinstance(child_edges, list):
                edge_count += sum(1 for edge in child_edges if isinstance(edge, dict))

            child_nodes, child_edge_count = cls._flatten_ir_nodes(node.get("children"), parent_id=node_id or parent_id)
            nodes.extend(child_nodes)
            edge_count += child_edge_count

        return nodes, edge_count

    @staticmethod
    def _build_report_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(report, dict):
            return None

        warnings = report.get("warnings")
        errors = report.get("errors")
        return {
            "workflow_name": report.get("workflow_name") or "",
            "supported": bool(report.get("supported", False)),
            "total_nodes": int(report.get("total_nodes") or 0),
            "mapped_count": int(report.get("mapped_count") or 0),
            "partial_count": int(report.get("partial_count") or 0),
            "unmappable_count": int(report.get("unmappable_count") or 0),
            "skipped_count": int(report.get("skipped_count") or 0),
            "warnings_count": len(warnings) if isinstance(warnings, list) else 0,
            "errors_count": len(errors) if isinstance(errors, list) else 0,
        }

    @staticmethod
    def _build_write_result(
        *,
        mode: str,
        app_id: str | None,
        target_db_url: str,
        written_at: datetime,
        status: str,
        error: str | None = None,
        requested_app_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "app_id": app_id,
            "mode": mode,
            "status": status,
            "error": error,
            "requested_app_id": requested_app_id,
            "target": build_database_ref(target_db_url),
            "written_at": written_at.isoformat(),
        }

    @staticmethod
    def _serialize_write_result(write_result: Any) -> dict[str, Any] | None:
        if not isinstance(write_result, dict):
            return None

        target = write_result.get("target")
        if not isinstance(target, dict):
            target = build_database_ref(write_result.get("db_url"))

        return {
            "app_id": write_result.get("app_id"),
            "mode": write_result.get("mode"),
            "status": write_result.get("status") or ("failed" if write_result.get("error") else "succeeded"),
            "error": write_result.get("error"),
            "requested_app_id": write_result.get("requested_app_id"),
            "target": target,
            "written_at": write_result.get("written_at"),
        }

    @classmethod
    def _serialize_audit(cls, audit: Any, task: MigrationTask) -> dict[str, Any]:
        payload = dict(audit) if isinstance(audit, dict) else {}
        source = payload.get("source")
        if not isinstance(source, dict):
            source = {}

        payload["source"] = {
            "type": source.get("type") or task.source_type,
            "workflow_id": source.get("workflow_id") or task.source_workflow_id,
            "workflow_name": source.get("workflow_name") or task.source_workflow_name,
        }

        payload["last_write"] = cls._serialize_write_result(payload.get("last_write"))
        if payload["last_write"] is None and isinstance(task.ir_snapshot, dict):
            payload["last_write"] = cls._serialize_write_result(task.ir_snapshot.get("write_result"))

        return payload

    @classmethod
    def _extract_canvas(cls, payload: Any) -> dict[str, Any]:
        candidates: list[Any] = [payload]
        if isinstance(payload, dict):
            candidates.extend(
                [
                    payload.get("data"),
                    payload.get("workflow"),
                    payload.get("data", {}).get("workflow") if isinstance(payload.get("data"), dict) else None,
                ]
            )

        for candidate in candidates:
            canvas = cls._coerce_canvas(candidate)
            if canvas is not None:
                return canvas

        raise ValueError("Unsupported Coze workflow payload shape")

    @classmethod
    def _coerce_canvas(cls, payload: Any) -> dict[str, Any] | None:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return None

        if not isinstance(payload, dict):
            return None

        if "nodes" in payload and "edges" in payload:
            return payload

        for key in ("canvas", "schema_json"):
            value = payload.get(key)
            if isinstance(value, dict) and "nodes" in value and "edges" in value:
                return value
            if isinstance(value, str):
                try:
                    decoded = json.loads(value)
                except json.JSONDecodeError:
                    continue
                if isinstance(decoded, dict) and "nodes" in decoded and "edges" in decoded:
                    return decoded

        return None
