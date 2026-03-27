from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from db.models import MigrationTask

from .data import WORKFLOWS


class WorkbenchOverviewProvider:
    def load_demo_workflows(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return deepcopy(WORKFLOWS[:limit])

    def has_persisted_workflows(self, db: Session | None) -> bool:
        if db is None:
            return False
        return db.query(MigrationTask.id).filter(MigrationTask.sync_config_id.is_(None)).first() is not None

    def load_persisted_workflows(self, db: Session, *, limit: int) -> list[dict[str, Any]]:
        tasks = (
            db.query(MigrationTask)
            .filter(MigrationTask.sync_config_id.is_(None))
            .order_by(
                MigrationTask.completed_at.desc(),
                MigrationTask.created_at.desc(),
                MigrationTask.id.desc(),
            )
            .limit(limit)
            .all()
        )
        return [self._serialize_task(task) for task in tasks]

    def has_persisted_workflow(self, db: Session, workflow_id: str) -> bool:
        return self.find_persisted_task(db, workflow_id) is not None

    def find_persisted_task(self, db: Session, workflow_id: str) -> MigrationTask | None:
        task = (
            db.query(MigrationTask)
            .filter(MigrationTask.sync_config_id.is_(None))
            .filter(MigrationTask.source_workflow_id == workflow_id)
            .order_by(MigrationTask.id.desc())
            .first()
        )
        if task is not None or not workflow_id.isdigit():
            return task
        return (
            db.query(MigrationTask)
            .filter(MigrationTask.sync_config_id.is_(None))
            .filter(MigrationTask.id == int(workflow_id))
            .first()
        )

    def _serialize_task(self, task: MigrationTask) -> dict[str, Any]:
        report = task.report or {}
        snapshot = task.ir_snapshot or {}
        write_result = snapshot.get("write_result") if isinstance(snapshot, dict) else None
        if not isinstance(write_result, dict):
            write_result = {}

        nodes = int(report.get("total_nodes") or 0)
        mapped = int(report.get("mapped_count") or 0)
        partial = int(report.get("partial_count") or 0)
        skipped = int(report.get("skipped_count") or 0)
        migrated = mapped + partial
        failed = max(nodes - migrated - skipped, 0)
        score = 0.0
        if nodes > 0:
            score = round(((mapped + (partial * 0.5)) / nodes) * 100, 1)

        source_workflow_id = _coerce_optional_string(task.source_workflow_id) or str(task.id)
        return {
            "id": source_workflow_id,
            "conversionId": str(task.id),
            "name": str(report.get("workflow_name") or task.source_workflow_name or task.source_workflow_id or task.id),
            "cozeId": source_workflow_id,
            "difyId": _coerce_optional_string(write_result.get("app_id")),
            "status": self._derive_status(
                task_status=task.status,
                supported=bool(report.get("supported", False)),
                requires_manual_review=bool(report.get("requires_manual_review", False)),
                write_status=str(write_result.get("status") or ""),
            ),
            "nodes": nodes,
            "migrated": migrated,
            "failed": failed,
            "score": score,
            "complexity": self._derive_complexity(nodes),
            "lastSync": task.completed_at.isoformat() if task.completed_at else None,
            "sourceType": task.source_type,
            "requiresManualReview": bool(report.get("requires_manual_review", False)),
        }

    @staticmethod
    def _derive_status(
        *,
        task_status: str,
        supported: bool,
        requires_manual_review: bool,
        write_status: str,
    ) -> str:
        if task_status in {"failed", "blocked", "write_failed"} or not supported:
            return "failed"
        if write_status == "succeeded" and task_status in {"written", "updated"}:
            return "verified"
        if task_status in {"pending", "running"}:
            return "pending"
        if requires_manual_review:
            return "testing"
        return "migrated"

    @staticmethod
    def _derive_complexity(nodes: int) -> str:
        if nodes >= 12:
            return "high"
        if nodes >= 7:
            return "medium"
        return "low"


def _coerce_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str or None
