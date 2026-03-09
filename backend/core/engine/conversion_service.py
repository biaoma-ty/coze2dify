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
        snapshot = task.ir_snapshot or {}
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
            "report": task.report or {},
            "write_result": snapshot.get("write_result"),
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

        snapshot = task.ir_snapshot or {}
        dsl_payload = snapshot.get("dify_dsl")
        if dsl_payload is None:
            if not task.dify_dsl:
                raise LookupError(f"Conversion {conversion_id} has no DSL artifact")
            dsl_payload = yaml.safe_load(task.dify_dsl)

        dify_dsl = DifyDSL.model_validate(dsl_payload)
        writer = DifyDbWriter(target_db_url)
        if app_id:
            writer.update_workflow(app_id, dify_dsl)
            mode = "update"
            target_app_id = app_id
        else:
            target_app_id = writer.write_workflow(dify_dsl)
            mode = "create"

        snapshot["write_result"] = {
            "app_id": target_app_id,
            "mode": mode,
            "db_url": target_db_url,
            "written_at": datetime.now(timezone.utc).isoformat(),
        }
        task.ir_snapshot = snapshot
        task.status = "updated" if mode == "update" else "written"
        task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "conversion_id": str(task.id),
            "app_id": target_app_id,
            "mode": mode,
            "status": task.status,
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
        yaml_output = self.engine.dify_generator.to_yaml(dify_dsl)
        snapshot = {
            "ir_workflow": ir_workflow.model_dump(mode="json"),
            "dify_dsl": dify_dsl.model_dump(mode="json"),
            "write_result": None,
        }
        task = MigrationTask(
            source_type=source_type,
            source_workflow_id=source_workflow_id,
            source_workflow_name=source_workflow_name,
            status="converted",
            ir_snapshot=snapshot,
            dify_dsl=yaml_output,
            report=report.model_dump(mode="json"),
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
            "write_result": write_result,
            "report_summary": cls._build_report_summary(task.report),
        }

    @staticmethod
    def _build_report_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(report, dict):
            return None

        warnings = report.get("warnings")
        errors = report.get("errors")
        return {
            "workflow_name": report.get("workflow_name") or "",
            "total_nodes": int(report.get("total_nodes") or 0),
            "mapped_count": int(report.get("mapped_count") or 0),
            "partial_count": int(report.get("partial_count") or 0),
            "unmappable_count": int(report.get("unmappable_count") or 0),
            "skipped_count": int(report.get("skipped_count") or 0),
            "warnings_count": len(warnings) if isinstance(warnings, list) else 0,
            "errors_count": len(errors) if isinstance(errors, list) else 0,
        }

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
