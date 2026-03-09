from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.coze.db_reader import CozeDbReader
from core.dify.db_reader import DifyDbReader
from core.engine.conversion_service import ConversionService
from core.sync.conflict_resolver import ConflictResolver, ConflictStrategy
from core.sync.diff_detector import DiffDetector
from db.models import MigrationTask, SyncConfig, SyncHistory


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SyncEngine:
    """Execute a manual Coze -> Dify sync using the existing conversion/write path."""

    def __init__(
        self,
        conversion_service: ConversionService | None = None,
        *,
        coze_reader_factory: Callable[[str], CozeDbReader] = CozeDbReader,
        dify_reader_factory: Callable[[str], DifyDbReader] = DifyDbReader,
        diff_detector: DiffDetector | None = None,
        conflict_resolver: ConflictResolver | None = None,
    ) -> None:
        self.conversion_service = conversion_service or ConversionService()
        self.coze_reader_factory = coze_reader_factory
        self.dify_reader_factory = dify_reader_factory
        self.diff_detector = diff_detector or DiffDetector()
        self.conflict_resolver = conflict_resolver or ConflictResolver()

    def execute_sync(
        self,
        db: Session,
        config: SyncConfig,
        *,
        trigger_type: str = "manual",
    ) -> dict[str, Any]:
        history = SyncHistory(
            sync_config_id=config.id,
            trigger_type=trigger_type,
            status="running",
            started_at=_utcnow(),
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        summary = self._empty_summary()
        items: list[dict[str, Any]] = []
        status = "completed"

        try:
            source_workflows = self.coze_reader_factory(config.coze_db_url).list_workflows()
            dify_reader = self.dify_reader_factory(config.dify_db_url)
            target_apps = dify_reader.list_apps()

            mappings = self._load_existing_mappings(db, config.id)
            duplicate_target_app_ids = self._find_duplicate_target_app_ids(mappings)
            source_ids = {self._workflow_id(workflow) for workflow in source_workflows if self._workflow_id(workflow)}
            target_apps_by_id = {str(app.get("app_id") or ""): app for app in target_apps if app.get("app_id")}
            target_names = self._index_target_names(target_apps)

            items.extend(self._collect_delete_gaps(mappings, source_ids, target_apps_by_id, summary))

            for workflow in source_workflows:
                source_id = self._workflow_id(workflow)
                source_name = str(workflow.get("name") or source_id or "Unknown workflow")

                if not source_id:
                    items.append(
                        self._result_item(
                            action="inspect",
                            status="failed",
                            source_workflow_id="",
                            source_workflow_name=source_name,
                            message="Coze workflow is missing workflow_id; manual sync cannot continue safely.",
                        )
                    )
                    summary["failed"] += 1
                    continue

                mapping = mappings.get(source_id)
                if mapping and mapping["app_id"] in duplicate_target_app_ids:
                    items.append(
                        self._result_item(
                            action="update",
                            status="conflict",
                            source_workflow_id=source_id,
                            source_workflow_name=source_name,
                            target_app_id=mapping["app_id"],
                            message=(
                                "Multiple source workflows point to the same Dify app. "
                                "Manual sync skipped this workflow to avoid writing to the wrong target."
                            ),
                        )
                    )
                    summary["conflicts"] += 1
                    continue

                if mapping is None:
                    name_matches = target_names.get(self._normalize_name(source_name), [])
                    if name_matches:
                        message = (
                            "Found an existing Dify app with the same name but no established sync mapping."
                            if len(name_matches) == 1
                            else "Found multiple Dify apps with the same name and no established sync mapping."
                        )
                        items.append(
                            self._result_item(
                                action="create",
                                status="conflict",
                                source_workflow_id=source_id,
                                source_workflow_name=source_name,
                                target_app_id=name_matches[0]["app_id"] if len(name_matches) == 1 else None,
                                message=f"{message} Manual sync requires a stable prior mapping before updating.",
                            )
                        )
                        summary["conflicts"] += 1
                        continue

                action = "update" if mapping and mapping["app_id"] in target_apps_by_id else "create"

                try:
                    conversion = self.conversion_service.convert_from_db(
                        db,
                        db_url=config.coze_db_url,
                        workflow_id=source_id,
                    )
                    conversion_id = str(conversion["conversion_id"])
                    self._attach_sync_config(db, conversion_id, config.id)

                    target_app_id = mapping["app_id"] if mapping else None
                    if action == "update":
                        target_workflow = dify_reader.read_workflow(target_app_id)
                        if target_workflow is None:
                            action = "create"
                        elif self._is_unchanged(conversion, target_workflow):
                            items.append(
                                self._result_item(
                                    action="skip",
                                    status="skipped",
                                    source_workflow_id=source_id,
                                    source_workflow_name=source_name,
                                    target_app_id=target_app_id,
                                    conversion_id=conversion_id,
                                    message="No changes detected between the converted workflow and the current Dify target.",
                                )
                            )
                            summary["skipped"] += 1
                            continue

                    write_result = self.conversion_service.write_to_dify(
                        db,
                        conversion_id,
                        db_url=config.dify_db_url,
                        app_id=target_app_id if action == "update" else None,
                    )
                    final_action = "updated" if write_result["mode"] == "update" else "created"
                    summary[final_action] += 1
                    items.append(
                        self._result_item(
                            action=write_result["mode"],
                            status=final_action,
                            source_workflow_id=source_id,
                            source_workflow_name=source_name,
                            target_app_id=write_result["app_id"],
                            conversion_id=conversion_id,
                            message=(
                                "Updated existing Dify workflow via the persisted sync mapping."
                                if write_result["mode"] == "update"
                                else "Created a new Dify workflow from the converted Coze source."
                            ),
                        )
                    )
                except Exception as exc:  # noqa: BLE001 - preserve run history instead of failing the whole request
                    items.append(
                        self._result_item(
                            action=action,
                            status="failed",
                            source_workflow_id=source_id,
                            source_workflow_name=source_name,
                            target_app_id=mapping["app_id"] if mapping else None,
                            message=str(exc),
                        )
                    )
                    summary["failed"] += 1
        except Exception as exc:  # noqa: BLE001 - persist run-level failure details
            items.append(
                self._result_item(
                    action="inspect",
                    status="failed",
                    source_workflow_id="",
                    source_workflow_name=config.name,
                    message=str(exc),
                )
            )
            summary["failed"] += 1
            status = "failed"

        if status != "failed":
            status = self._derive_status(summary)

        history.workflows_synced = summary["created"] + summary["updated"]
        history.workflows_failed = summary["failed"]
        history.conflicts_count = summary["conflicts"]
        history.conflicts_resolved = {"summary": summary, "items": items}
        history.completed_at = _utcnow()
        history.status = status
        db.add(history)
        db.commit()
        db.refresh(history)

        return self.serialize_history(history, include_items=True)

    def preview_diff(self, db: Session, config: SyncConfig) -> dict[str, Any]:
        summary = self._empty_summary()
        items: list[dict[str, Any]] = []

        source_reader = self.coze_reader_factory(config.coze_db_url)
        dify_reader = self.dify_reader_factory(config.dify_db_url)
        source_workflows = source_reader.list_workflows()
        target_apps = dify_reader.list_apps()
        mappings = self._load_existing_mappings(db, config.id)
        duplicate_target_app_ids = self._find_duplicate_target_app_ids(mappings)
        source_ids = {self._workflow_id(workflow) for workflow in source_workflows if self._workflow_id(workflow)}
        target_apps_by_id = {str(app.get("app_id") or ""): app for app in target_apps if app.get("app_id")}
        target_names = self._index_target_names(target_apps)

        items.extend(self._collect_delete_gaps(mappings, source_ids, target_apps_by_id, summary))

        source_snapshots: dict[str, dict[str, Any]] = {}
        target_snapshots: dict[str, dict[str, Any]] = {}
        candidates: dict[str, dict[str, Any]] = {}

        for workflow in source_workflows:
            source_id = self._workflow_id(workflow)
            source_name = str(workflow.get("name") or source_id or "Unknown workflow")

            if not source_id:
                items.append(
                    self._result_item(
                        action="inspect",
                        status="failed",
                        source_workflow_id="",
                        source_workflow_name=source_name,
                        message="Coze workflow is missing workflow_id; diff preview cannot continue safely.",
                    )
                )
                summary["failed"] += 1
                continue

            mapping = mappings.get(source_id)
            if mapping and mapping["app_id"] in duplicate_target_app_ids:
                items.append(
                    self._result_item(
                        action="update",
                        status="conflict",
                        source_workflow_id=source_id,
                        source_workflow_name=source_name,
                        target_app_id=mapping["app_id"],
                        message="Multiple source workflows map to the same Dify app. Resolve the mapping before syncing.",
                    )
                )
                summary["conflicts"] += 1
                continue

            if mapping is None:
                name_matches = target_names.get(self._normalize_name(source_name), [])
                if name_matches:
                    items.append(
                        self._result_item(
                            action="create",
                            status="conflict",
                            source_workflow_id=source_id,
                            source_workflow_name=source_name,
                            target_app_id=name_matches[0]["app_id"] if len(name_matches) == 1 else None,
                            message=(
                                "Found existing Dify app names that collide with this workflow. "
                                "Resolve the conflict before syncing."
                            ),
                        )
                    )
                    summary["conflicts"] += 1
                    continue

            try:
                converted = self._convert_source_workflow(source_reader, source_id)
            except Exception as exc:  # noqa: BLE001 - diff preview should surface actionable failures
                items.append(
                    self._result_item(
                        action="inspect",
                        status="failed",
                        source_workflow_id=source_id,
                        source_workflow_name=source_name,
                        target_app_id=mapping["app_id"] if mapping else None,
                        message=str(exc),
                    )
                )
                summary["failed"] += 1
                continue

            source_snapshots[source_id] = self._normalized_dsl_payload(converted["dsl"])
            if mapping and mapping["app_id"] in target_apps_by_id:
                target_workflow = dify_reader.read_workflow(mapping["app_id"])
                if target_workflow is not None:
                    target_snapshots[source_id] = self._normalized_target_payload(target_workflow)

            candidates[source_id] = {
                "source_workflow_name": converted["source_workflow_name"] or source_name,
                "target_app_id": mapping["app_id"] if mapping else None,
                "had_mapping": bool(mapping),
                "target_exists": bool(mapping and mapping["app_id"] in target_apps_by_id),
            }

        new_ids, updated_ids, _ = self.diff_detector.detect_changes(source_snapshots, target_snapshots)
        new_set = set(new_ids)
        updated_set = set(updated_ids)
        unchanged_set = (set(source_snapshots) & set(target_snapshots)) - updated_set

        for workflow in source_workflows:
            source_id = self._workflow_id(workflow)
            if source_id not in candidates:
                continue

            candidate = candidates[source_id]
            source_name = str(candidate["source_workflow_name"] or workflow.get("name") or source_id)
            target_app_id = candidate["target_app_id"]
            had_mapping = bool(candidate["had_mapping"])
            target_exists = bool(candidate["target_exists"])

            if source_id in new_set:
                summary["created"] += 1
                message = (
                    "Existing sync mapping points to a missing Dify app. The next sync run will recreate it."
                    if had_mapping and not target_exists
                    else "No matching Dify app was found. The next sync run will create one."
                )
                items.append(
                    self._result_item(
                        action="create",
                        status="created",
                        source_workflow_id=source_id,
                        source_workflow_name=source_name,
                        target_app_id=target_app_id if target_exists else None,
                        message=message,
                    )
                )
            elif source_id in updated_set:
                summary["updated"] += 1
                items.append(
                    self._result_item(
                        action="update",
                        status="updated",
                        source_workflow_id=source_id,
                        source_workflow_name=source_name,
                        target_app_id=target_app_id,
                        message="Diff preview detected changes between the converted source workflow and the Dify target.",
                    )
                )
            elif source_id in unchanged_set:
                summary["skipped"] += 1
                items.append(
                    self._result_item(
                        action="skip",
                        status="skipped",
                        source_workflow_id=source_id,
                        source_workflow_name=source_name,
                        target_app_id=target_app_id,
                        message="No changes detected between the converted source workflow and the current Dify target.",
                    )
                )

        return {
            "config_id": config.id,
            "summary": summary,
            "items": items,
            "status": self._derive_status(summary),
        }

    def resolve_conflict(
        self,
        db: Session,
        history: SyncHistory,
        *,
        conflict_id: str,
        strategy: ConflictStrategy,
    ) -> dict[str, Any]:
        payload = history.conflicts_resolved or {}
        items = list(payload.get("items") or [])
        summary = {
            **self._empty_summary(),
            **(payload.get("summary") or {}),
        }
        config = history.sync_config
        if config is None:
            raise LookupError(f"Sync config {history.sync_config_id} not found")

        index = next(
            (
                idx
                for idx, item in enumerate(items)
                if item.get("source_workflow_id") == conflict_id and item.get("status") == "conflict"
            ),
            None,
        )
        if index is None:
            raise LookupError(f"Conflict {conflict_id} not found in sync history {history.id}")

        conflict_item = dict(items[index])
        target_app_id = conflict_item.get("target_app_id")
        source_reader = self.coze_reader_factory(config.coze_db_url)
        dify_reader = self.dify_reader_factory(config.dify_db_url)

        source_payload = source_reader.read_workflow(conflict_id)
        if source_payload is None:
            raise LookupError(f"Workflow {conflict_id} not found in Coze database")

        target_payload = dify_reader.read_workflow(target_app_id) if target_app_id else {}
        resolved_payload = self.conflict_resolver.resolve(
            conflict_id,
            source_payload,
            target_payload or {},
            strategy,
        )

        if strategy == ConflictStrategy.MANUAL:
            conflict_item["resolution"] = {
                "strategy": strategy.value,
                "resolved_at": _utcnow().isoformat(),
                "status": "pending_manual_review",
            }
            items[index] = conflict_item
            history.conflicts_resolved = {"summary": summary, "items": items}
            db.add(history)
            db.commit()
            db.refresh(history)
            return self.serialize_history(history, include_items=True)

        summary["conflicts"] = max(0, int(summary.get("conflicts") or 0) - 1)

        if strategy == ConflictStrategy.TARGET_WINS or resolved_payload is None:
            summary["skipped"] += 1
            conflict_item.update(
                {
                    "action": "keep",
                    "status": "skipped",
                    "message": "Conflict resolved by keeping the existing Dify target unchanged.",
                    "resolution": {
                        "strategy": strategy.value,
                        "resolved_at": _utcnow().isoformat(),
                        "status": "kept_target",
                    },
                }
            )
        else:
            write_result = self._resolve_conflict_with_source(
                db,
                config,
                conflict_id=conflict_id,
                target_app_id=target_app_id,
            )
            final_status = "updated" if write_result["mode"] == "update" else "created"
            summary[final_status] += 1
            history.workflows_synced += 1
            conflict_item.update(
                {
                    "action": write_result["mode"],
                    "status": final_status,
                    "target_app_id": write_result["app_id"],
                    "conversion_id": write_result["conversion_id"],
                    "message": (
                        "Conflict resolved by applying the source workflow to the existing Dify target."
                        if write_result["mode"] == "update"
                        else "Conflict resolved by creating a fresh Dify workflow from the source."
                    ),
                    "resolution": {
                        "strategy": strategy.value,
                        "resolved_at": _utcnow().isoformat(),
                        "status": "applied_source",
                    },
                }
            )

        items[index] = conflict_item
        history.workflows_failed = summary["failed"]
        history.conflicts_count = summary["conflicts"]
        history.conflicts_resolved = {"summary": summary, "items": items}
        history.completed_at = _utcnow()
        history.status = self._derive_status(summary)
        db.add(history)
        db.commit()
        db.refresh(history)
        return self.serialize_history(history, include_items=True)

    @staticmethod
    def serialize_history(history: SyncHistory, *, include_items: bool = False) -> dict[str, Any]:
        payload = history.conflicts_resolved or {}
        summary = payload.get("summary") or SyncEngine._empty_summary()
        data = {
            "id": str(history.id),
            "sync_config_id": history.sync_config_id,
            "sync_config_name": history.sync_config.name if history.sync_config else None,
            "trigger_type": history.trigger_type,
            "status": history.status,
            "started_at": history.started_at.isoformat() if history.started_at else None,
            "completed_at": history.completed_at.isoformat() if history.completed_at else None,
            "workflows_synced": history.workflows_synced,
            "workflows_failed": history.workflows_failed,
            "conflicts_count": history.conflicts_count,
            "summary": {
                **SyncEngine._empty_summary(),
                **summary,
            },
        }
        if include_items:
            data["items"] = payload.get("items") or []
        return data

    @staticmethod
    def _empty_summary() -> dict[str, int]:
        return {
            "created": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0,
            "unsupported": 0,
            "conflicts": 0,
        }

    @classmethod
    def _derive_status(cls, summary: dict[str, int]) -> str:
        if summary["failed"] > 0 and summary["created"] == 0 and summary["updated"] == 0:
            return "failed"
        if summary["failed"] > 0 or summary["unsupported"] > 0 or summary["conflicts"] > 0:
            return "partial"
        return "completed"

    @staticmethod
    def _result_item(
        *,
        action: str,
        status: str,
        source_workflow_id: str,
        source_workflow_name: str,
        message: str,
        target_app_id: str | None = None,
        conversion_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "action": action,
            "status": status,
            "source_workflow_id": source_workflow_id,
            "source_workflow_name": source_workflow_name,
            "target_app_id": target_app_id,
            "conversion_id": conversion_id,
            "message": message,
        }

    @staticmethod
    def _workflow_id(workflow: dict[str, Any]) -> str:
        return str(workflow.get("id") or workflow.get("workflow_id") or workflow.get("bot_id") or "")

    @staticmethod
    def _normalize_name(value: str) -> str:
        return value.strip().casefold()

    @classmethod
    def _index_target_names(cls, target_apps: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        index: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for app in target_apps:
            normalized = cls._normalize_name(str(app.get("name") or ""))
            if normalized:
                index[normalized].append(app)
        return index

    @staticmethod
    def _attach_sync_config(db: Session, conversion_id: str, sync_config_id: int) -> None:
        task = db.get(MigrationTask, int(conversion_id))
        if task is None:
            return
        task.sync_config_id = sync_config_id
        db.add(task)
        db.commit()

    @staticmethod
    def _fingerprint(payload: Any) -> str:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    @classmethod
    def _is_unchanged(cls, conversion: dict[str, Any], target_workflow: dict[str, Any]) -> bool:
        return cls._fingerprint(cls._normalized_dsl_payload(conversion.get("dsl") or {})) == cls._fingerprint(
            cls._normalized_target_payload(target_workflow)
        )

    def _resolve_conflict_with_source(
        self,
        db: Session,
        config: SyncConfig,
        *,
        conflict_id: str,
        target_app_id: str | None,
    ) -> dict[str, Any]:
        conversion = self.conversion_service.convert_from_db(
            db,
            db_url=config.coze_db_url,
            workflow_id=conflict_id,
        )
        conversion_id = str(conversion["conversion_id"])
        self._attach_sync_config(db, conversion_id, config.id)
        return self.conversion_service.write_to_dify(
            db,
            conversion_id,
            db_url=config.dify_db_url,
            app_id=target_app_id,
        )

    def _convert_source_workflow(self, source_reader: CozeDbReader, workflow_id: str) -> dict[str, Any]:
        payload = source_reader.read_workflow(workflow_id)
        if payload is None:
            raise LookupError(f"Workflow {workflow_id} not found in Coze database")

        canvas = self.conversion_service._extract_canvas(payload)
        ir_workflow = self.conversion_service.engine.coze_parser.parse_dict(canvas)
        dify_dsl, _report = self.conversion_service.engine.convert_from_ir(ir_workflow)
        source_workflow_name = ""
        if isinstance(payload, dict):
            source_workflow_name = str(payload.get("name") or "")
        return {
            "dsl": dify_dsl.model_dump(mode="json"),
            "source_workflow_name": source_workflow_name or ir_workflow.name or workflow_id,
        }

    @staticmethod
    def _normalized_dsl_payload(dsl_payload: dict[str, Any]) -> dict[str, Any]:
        workflow_payload = dsl_payload.get("workflow") if isinstance(dsl_payload, dict) else {}
        return {
            "graph": workflow_payload.get("graph"),
            "features": workflow_payload.get("features") or {},
        }

    @staticmethod
    def _normalized_target_payload(target_workflow: dict[str, Any]) -> dict[str, Any]:
        return {
            "graph": target_workflow.get("graph"),
            "features": target_workflow.get("features") or {},
        }

    @staticmethod
    def _find_duplicate_target_app_ids(mappings: dict[str, dict[str, Any]]) -> set[str]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for source_id, mapping in mappings.items():
            target_app_id = mapping["app_id"]
            if target_app_id:
                grouped[target_app_id].append(source_id)
        return {app_id for app_id, source_ids in grouped.items() if len(source_ids) > 1}

    @staticmethod
    def _load_existing_mappings(db: Session, sync_config_id: int) -> dict[str, dict[str, Any]]:
        stmt = (
            select(MigrationTask)
            .where(MigrationTask.sync_config_id == sync_config_id)
            .order_by(MigrationTask.completed_at.desc(), MigrationTask.id.desc())
        )
        tasks = db.execute(stmt).scalars().all()
        mappings: dict[str, dict[str, Any]] = {}

        for task in tasks:
            source_id = str(task.source_workflow_id or "")
            if not source_id or source_id in mappings:
                continue
            snapshot = task.ir_snapshot or {}
            write_result = snapshot.get("write_result") if isinstance(snapshot, dict) else None
            app_id = str(write_result.get("app_id") or "") if isinstance(write_result, dict) else ""
            if not app_id:
                continue
            mappings[source_id] = {
                "app_id": app_id,
                "task_id": task.id,
                "source_workflow_name": task.source_workflow_name,
            }

        return mappings

    @classmethod
    def _collect_delete_gaps(
        cls,
        mappings: dict[str, dict[str, Any]],
        source_ids: set[str],
        target_apps_by_id: dict[str, dict[str, Any]],
        summary: dict[str, int],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for source_id, mapping in mappings.items():
            if source_id in source_ids:
                continue
            target_app_id = mapping["app_id"]
            if target_app_id not in target_apps_by_id:
                continue
            summary["unsupported"] += 1
            items.append(
                cls._result_item(
                    action="delete",
                    status="unsupported",
                    source_workflow_id=source_id,
                    source_workflow_name=str(mapping.get("source_workflow_name") or source_id),
                    target_app_id=target_app_id,
                    message="Delete sync is not supported in the manual sync MVP. The existing Dify app was left untouched.",
                )
            )
        return items
