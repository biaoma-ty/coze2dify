from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from db.models import MigrationTask


@dataclass(frozen=True)
class WorkflowOverviewItem:
    id: str
    conversion_id: str
    name: str
    coze_id: str
    dify_id: str | None
    status: str
    nodes: int
    migrated: int
    failed: int
    score: float
    complexity: str
    last_sync: str | None
    source_type: str
    requires_manual_review: bool


class WorkbenchService:
    def get_overview(self, db: Session, *, limit: int = 50) -> dict[str, Any]:
        query = db.query(MigrationTask).filter(MigrationTask.sync_config_id.is_(None))
        tasks = (
            query.order_by(
                MigrationTask.completed_at.desc(),
                MigrationTask.created_at.desc(),
                MigrationTask.id.desc(),
            )
            .limit(limit)
            .all()
        )

        workflows = [self._serialize_workflow(task) for task in tasks]
        summary = self._build_summary(workflows)
        return {
            "summary": summary,
            "workflows": [workflow.__dict__ for workflow in workflows],
        }

    @staticmethod
    def _serialize_workflow(task: MigrationTask) -> WorkflowOverviewItem:
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

        status = WorkbenchService._derive_status(
            task_status=task.status,
            supported=bool(report.get("supported", False)),
            requires_manual_review=bool(report.get("requires_manual_review", False)),
            write_status=str(write_result.get("status") or ""),
        )

        return WorkflowOverviewItem(
            id=str(task.id),
            conversion_id=str(task.id),
            name=str(report.get("workflow_name") or task.source_workflow_name or task.source_workflow_id),
            coze_id=task.source_workflow_id,
            dify_id=_coerce_optional_string(write_result.get("app_id")),
            status=status,
            nodes=nodes,
            migrated=migrated,
            failed=failed,
            score=score,
            complexity=WorkbenchService._derive_complexity(nodes),
            last_sync=task.completed_at.isoformat() if task.completed_at else None,
            source_type=task.source_type,
            requires_manual_review=bool(report.get("requires_manual_review", False)),
        )

    @staticmethod
    def _build_summary(workflows: list[WorkflowOverviewItem]) -> dict[str, Any]:
        scored = [workflow.score for workflow in workflows if workflow.score > 0]
        total_nodes = sum(workflow.nodes for workflow in workflows)
        migrated_nodes = sum(workflow.migrated for workflow in workflows)
        failed_nodes = sum(workflow.failed for workflow in workflows)
        average_score = round(sum(scored) / len(scored), 1) if scored else 0.0

        return {
            "total_workflows": len(workflows),
            "verified_workflows": sum(1 for workflow in workflows if workflow.status == "verified"),
            "average_score": average_score,
            "total_nodes": total_nodes,
            "migrated_nodes": migrated_nodes,
            "failed_nodes": failed_nodes,
            "pending_reviews": sum(
                1 for workflow in workflows if workflow.requires_manual_review and workflow.status != "verified"
            ),
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
