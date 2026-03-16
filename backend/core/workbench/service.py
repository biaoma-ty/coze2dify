from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import Lock
from typing import Any

from sqlalchemy.orm import Session

from db.models import MigrationTask

from .data import (
    EQUIVALENCE,
    ERROR_PATTERNS,
    GENERATED_TEST_CASE,
    KNOWLEDGE_BASES,
    RELEASE_STATE,
    REVIEW_QUEUE,
    SANDBOX_METRICS,
    TEST_CASES,
    TOPOLOGY,
    WORKFLOWS,
)


class WorkbenchService:
    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._workflows = deepcopy(WORKFLOWS)
            self._workflow_overrides: dict[str, dict[str, Any]] = {}
            self._test_cases = deepcopy(TEST_CASES)
            self._review_queue = deepcopy(REVIEW_QUEUE)
            self._release_state: dict[str, dict[str, Any]] = {}
            self._sandbox_state: dict[str, dict[str, Any]] = {}

    def get_overview(self, db: Session | None = None, *, limit: int = 50) -> dict[str, Any]:
        workflows = self._get_visible_workflows(db, limit=limit)
        if db is not None and self._has_persisted_overview(db):
            pending_reviews = sum(1 for workflow in workflows if workflow.get("requiresManualReview"))
            return {
                "summary": self._build_summary(workflows, pending_reviews=pending_reviews),
                "workflows": workflows,
            }

        return {
            "summary": self._build_summary(workflows),
            "workflows": workflows,
        }

    def batch_migrate(self, db: Session | None = None, *, limit: int = 50) -> dict[str, Any]:
        with self._lock:
            if db is not None and self._has_persisted_overview(db):
                for workflow in self._load_persisted_overview(db, limit=limit):
                    if workflow["status"] == "pending":
                        self._workflow_overrides[workflow["id"]] = self._build_batch_migrate_patch(workflow)
            else:
                for workflow in self._workflows:
                    if workflow["status"] == "pending":
                        workflow.update(self._build_batch_migrate_patch(workflow))
        return self.get_overview(db, limit=limit)

    def get_topology(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        return deepcopy(TOPOLOGY)

    def get_equivalence(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        return deepcopy(EQUIVALENCE)

    def get_tests(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        return {
            "cases": deepcopy(self._test_cases),
            "patterns": self._build_error_patterns(),
        }

    def generate_tests(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        with self._lock:
            exists = any(item["id"] == GENERATED_TEST_CASE["id"] for item in self._test_cases)
            if not exists:
                self._test_cases.append(deepcopy(GENERATED_TEST_CASE))
        payload = self.get_tests(workflow_id, db)
        payload["generated"] = 0 if exists else 1
        return payload

    def run_tests(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        payload = self.get_tests(workflow_id, db)
        payload["executed"] = len(payload["cases"])
        payload["lastRunAt"] = "2026-03-13T00:00:00"
        return payload

    def get_knowledge(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        return {"records": deepcopy(KNOWLEDGE_BASES)}

    def get_review_queue(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        return {"items": deepcopy(self._review_queue)}

    def update_review_verdict(
        self,
        workflow_id: str,
        review_id: str,
        verdict: str,
        db: Session | None = None,
    ) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        with self._lock:
            review = next((item for item in self._review_queue if item["id"] == review_id), None)
            if review is None:
                raise LookupError(f"Unknown review item: {review_id}")
            review["verdict"] = verdict
            item = deepcopy(review)
            items = deepcopy(self._review_queue)
        return {
            "item": item,
            "items": items,
            "summary": self.get_overview(db)["summary"],
        }

    def get_release(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        with self._lock:
            state = self._release_state.setdefault(workflow_id, deepcopy(RELEASE_STATE))
            return deepcopy(state)

    def update_traffic(
        self,
        workflow_id: str,
        traffic: int,
        db: Session | None = None,
    ) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        if traffic < 0 or traffic > 100:
            raise ValueError("Traffic must be between 0 and 100")
        with self._lock:
            state = self._release_state.setdefault(workflow_id, deepcopy(RELEASE_STATE))
            state["traffic"] = traffic
            state["stages"] = self._build_stages(traffic)
            return deepcopy(state)

    def rollback_release(
        self,
        workflow_id: str,
        version: str | None = None,
        db: Session | None = None,
    ) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        with self._lock:
            state = self._release_state.setdefault(workflow_id, deepcopy(RELEASE_STATE))
            target = version or next(
                (item["ver"] for item in state["versions"] if item["st"] == "rollback"),
                None,
            )
            if target is None:
                raise LookupError("No rollback version available")

            current_active = next(
                (item["ver"] for item in state["versions"] if item["st"] == "active"),
                None,
            )
            matched = False
            for item in state["versions"]:
                if item["ver"] == target:
                    item["st"] = "active"
                    matched = True
                elif item["ver"] == current_active:
                    item["st"] = "rollback"
                elif item["st"] != "archived":
                    item["st"] = "archived"

            if not matched:
                raise LookupError(f"Unknown rollback version: {target}")

            state["traffic"] = 20
            state["stages"] = self._build_stages(20)
            return deepcopy(state)

    def get_sandbox(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        with self._lock:
            state = self._sandbox_state.setdefault(
                workflow_id,
                {
                    "status": "idle",
                    "messages": [],
                    "requestCount": 0,
                    "counter": 0,
                },
            )
            return self._serialize_sandbox(state)

    def start_sandbox(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        with self._lock:
            state = self._sandbox_state.setdefault(
                workflow_id,
                {"status": "idle", "messages": [], "requestCount": 0, "counter": 0},
            )
            state["status"] = "running"
            return self._serialize_sandbox(state)

    def stop_sandbox(self, workflow_id: str, db: Session | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        with self._lock:
            state = self._sandbox_state.setdefault(
                workflow_id,
                {"status": "idle", "messages": [], "requestCount": 0, "counter": 0},
            )
            state["status"] = "idle"
            state["messages"] = []
            state["requestCount"] = 0
            state["counter"] = 0
            return self._serialize_sandbox(state)

    def send_sandbox_message(
        self,
        workflow_id: str,
        text: str,
        db: Session | None = None,
    ) -> dict[str, Any]:
        self._require_workflow(workflow_id, db)
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Message text is required")

        with self._lock:
            state = self._sandbox_state.setdefault(
                workflow_id,
                {"status": "idle", "messages": [], "requestCount": 0, "counter": 0},
            )
            if state["status"] != "running":
                raise ValueError("Sandbox session is not running")

            state["requestCount"] += 1
            state["messages"].append(self._build_message(state, "user", cleaned))
            coze_latency, dify_latency = self._latencies_for(cleaned)
            state["messages"].append(
                self._build_message(
                    state,
                    "coze",
                    self._reply_text(cleaned, "Coze"),
                    latency_ms=coze_latency,
                )
            )
            state["messages"].append(
                self._build_message(
                    state,
                    "dify",
                    self._reply_text(cleaned, "Dify"),
                    latency_ms=dify_latency,
                )
            )
            return self._serialize_sandbox(state)

    def _get_visible_workflows(
        self,
        db: Session | None = None,
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if db is not None and self._has_persisted_overview(db):
            workflows = self._load_persisted_overview(db, limit=limit)
            return self._apply_workflow_overrides(workflows)
        return deepcopy(self._workflows[:limit])

    def _load_persisted_overview(self, db: Session, *, limit: int) -> list[dict[str, Any]]:
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

    def _build_summary(
        self,
        workflows: list[dict[str, Any]],
        *,
        pending_reviews: int | None = None,
    ) -> dict[str, Any]:
        scored = [workflow["score"] for workflow in workflows if workflow["score"] > 0]
        total_nodes = sum(workflow["nodes"] for workflow in workflows)
        migrated_nodes = sum(workflow["migrated"] for workflow in workflows)
        failed_nodes = sum(workflow["failed"] for workflow in workflows)
        average_score = round(sum(scored) / len(scored), 1) if scored else 0.0

        if pending_reviews is None:
            pending_reviews = sum(1 for item in self._review_queue if item["verdict"] is None)

        return {
            "totalWorkflows": len(workflows),
            "verifiedWorkflows": sum(1 for workflow in workflows if workflow["status"] == "verified"),
            "averageScore": average_score,
            "totalNodes": total_nodes,
            "migratedNodes": migrated_nodes,
            "failedNodes": failed_nodes,
            "pendingReviews": pending_reviews,
        }

    def _build_error_patterns(self) -> list[dict[str, Any]]:
        patterns = deepcopy(ERROR_PATTERNS)
        counts: dict[str, int] = {}
        tests_by_pattern: dict[str, list[str]] = {}
        for case in self._test_cases:
            key = case.get("ep")
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1
            tests_by_pattern.setdefault(key, []).append(case["id"])

        for pattern in patterns:
            pattern["count"] = counts.get(pattern["key"], 0)
            pattern["tests"] = tests_by_pattern.get(pattern["key"], [])
        return patterns

    def _build_stages(self, traffic: int) -> list[dict[str, Any]]:
        stage_defs = [
            {"pct": 0, "label": "准备", "ts": "03/10"},
            {"pct": 5, "label": "5%", "ts": "03/10"},
            {"pct": 20, "label": "20%", "ts": "03/11"},
            {"pct": 50, "label": "50%", "ts": "—"},
            {"pct": 100, "label": "100%", "ts": "—"},
        ]
        active_index = 0
        for index, stage in enumerate(stage_defs):
            if traffic >= stage["pct"]:
                active_index = index

        stages: list[dict[str, Any]] = []
        for index, stage in enumerate(stage_defs):
            if index < active_index:
                status = "done"
            elif index == active_index:
                status = "active"
            else:
                status = "pending"
            ts = stage["ts"]
            if status == "active" and ts == "—":
                ts = datetime.now().strftime("%m/%d")
            stages.append({**stage, "st": status, "ts": ts})
        return stages

    def _serialize_sandbox(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": state["status"],
            "messages": deepcopy(state["messages"]),
            "metrics": self._build_metrics(state),
        }

    def _build_metrics(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        metrics = deepcopy(SANDBOX_METRICS)
        request_count = 142 + int(state["requestCount"])
        metrics[0]["coze"] = str(request_count)
        metrics[0]["dify"] = str(request_count)

        coze_latencies = [
            message["latencyMs"]
            for message in state["messages"]
            if message["role"] == "coze" and "latencyMs" in message
        ]
        dify_latencies = [
            message["latencyMs"]
            for message in state["messages"]
            if message["role"] == "dify" and "latencyMs" in message
        ]

        if coze_latencies:
            metrics[1]["coze"] = f"{(sum(coze_latencies) / len(coze_latencies)) / 1000:.1f}s"
        if dify_latencies:
            metrics[1]["dify"] = f"{(sum(dify_latencies) / len(dify_latencies)) / 1000:.1f}s"
        return metrics

    def _build_message(
        self,
        state: dict[str, Any],
        role: str,
        text: str,
        *,
        latency_ms: int | None = None,
    ) -> dict[str, Any]:
        state["counter"] += 1
        message: dict[str, Any] = {
            "id": f"{role}-{state['counter']}",
            "role": role,
            "text": text,
        }
        if latency_ms is not None:
            message["latencyMs"] = latency_ms
        return message

    def _reply_text(self, text: str, platform: str) -> str:
        short = text[:15]
        suffix = "…" if len(text) > 15 else ""
        return f"[{platform}] {short}{suffix}"

    def _latencies_for(self, text: str) -> tuple[int, int]:
        total = sum(ord(char) for char in text)
        return 800 + (total % 1201), 600 + (total % 1001)

    def _has_persisted_overview(self, db: Session) -> bool:
        return db.query(MigrationTask.id).filter(MigrationTask.sync_config_id.is_(None)).first() is not None

    def _find_persisted_task(self, db: Session, workflow_id: str) -> MigrationTask | None:
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

    def _apply_workflow_overrides(self, workflows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for workflow in workflows:
            override = self._workflow_overrides.get(workflow["id"])
            result.append({**workflow, **override} if override else workflow)
        return result

    @staticmethod
    def _build_batch_migrate_patch(workflow: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "testing",
            "difyId": workflow.get("difyId") or f"app-auto-{str(workflow['cozeId']).split('_')[-1]}",
            "migrated": workflow["nodes"],
            "failed": 0,
            "score": 96.4,
            "lastSync": "2026-03-13",
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

    def _require_workflow(self, workflow_id: str, db: Session | None = None) -> None:
        cleaned = workflow_id.strip()
        if not cleaned:
            raise LookupError("Unknown workflow: <empty>")
        if db is not None and self._has_persisted_overview(db):
            if self._find_persisted_task(db, cleaned) is None:
                raise LookupError(f"Unknown workflow: {cleaned}")
            return
        if not any(workflow["id"] == cleaned for workflow in self._workflows):
            raise LookupError(f"Unknown workflow: {cleaned}")


def _coerce_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str or None
