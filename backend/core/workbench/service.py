from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import Lock
from typing import Any

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
            self._test_cases = deepcopy(TEST_CASES)
            self._review_queue = deepcopy(REVIEW_QUEUE)
            self._release_state: dict[str, dict[str, Any]] = {}
            self._sandbox_state: dict[str, dict[str, Any]] = {}

    def get_overview(self, *, limit: int = 50) -> dict[str, Any]:
        workflows = deepcopy(self._workflows[:limit])
        return {
            "summary": self._build_summary(workflows),
            "workflows": workflows,
        }

    def batch_migrate(self) -> dict[str, Any]:
        with self._lock:
            for workflow in self._workflows:
                if workflow["status"] == "pending":
                    workflow["status"] = "testing"
                    workflow["difyId"] = f"app-auto-{workflow['cozeId'].split('_')[-1]}"
                    workflow["migrated"] = workflow["nodes"]
                    workflow["failed"] = 0
                    workflow["score"] = 96.4
                    workflow["lastSync"] = "2026-03-13"
            return self.get_overview()

    def get_topology(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        return deepcopy(TOPOLOGY)

    def get_equivalence(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        return deepcopy(EQUIVALENCE)

    def get_tests(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        return {
            "cases": deepcopy(self._test_cases),
            "patterns": self._build_error_patterns(),
        }

    def generate_tests(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        with self._lock:
            exists = any(item["id"] == GENERATED_TEST_CASE["id"] for item in self._test_cases)
            if not exists:
                self._test_cases.append(deepcopy(GENERATED_TEST_CASE))
        payload = self.get_tests(workflow_id)
        payload["generated"] = 0 if exists else 1
        return payload

    def run_tests(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        payload = self.get_tests(workflow_id)
        payload["executed"] = len(payload["cases"])
        payload["lastRunAt"] = "2026-03-13T00:00:00"
        return payload

    def get_knowledge(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        return {"records": deepcopy(KNOWLEDGE_BASES)}

    def get_review_queue(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        return {"items": deepcopy(self._review_queue)}

    def update_review_verdict(self, workflow_id: str, review_id: str, verdict: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        with self._lock:
            review = next((item for item in self._review_queue if item["id"] == review_id), None)
            if review is None:
                raise LookupError(f"Unknown review item: {review_id}")
            review["verdict"] = verdict
            return {
                "item": deepcopy(review),
                "items": deepcopy(self._review_queue),
                "summary": self._build_summary(self._workflows),
            }

    def get_release(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        with self._lock:
            state = self._release_state.setdefault(workflow_id, deepcopy(RELEASE_STATE))
            return deepcopy(state)

    def update_traffic(self, workflow_id: str, traffic: int) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        if traffic < 0 or traffic > 100:
            raise ValueError("Traffic must be between 0 and 100")
        with self._lock:
            state = self._release_state.setdefault(workflow_id, deepcopy(RELEASE_STATE))
            state["traffic"] = traffic
            state["stages"] = self._build_stages(traffic)
            return deepcopy(state)

    def rollback_release(self, workflow_id: str, version: str | None = None) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        with self._lock:
            state = self._release_state.setdefault(workflow_id, deepcopy(RELEASE_STATE))
            target = version or next(
                (item["ver"] for item in state["versions"] if item["st"] == "rollback"),
                None,
            )
            if target is None:
                raise LookupError("No rollback version available")

            current_active = next((item["ver"] for item in state["versions"] if item["st"] == "active"), None)
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

    def get_sandbox(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
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

    def start_sandbox(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
        with self._lock:
            state = self._sandbox_state.setdefault(
                workflow_id,
                {"status": "idle", "messages": [], "requestCount": 0, "counter": 0},
            )
            state["status"] = "running"
            return self._serialize_sandbox(state)

    def stop_sandbox(self, workflow_id: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
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

    def send_sandbox_message(self, workflow_id: str, text: str) -> dict[str, Any]:
        self._require_workflow(workflow_id)
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

    def _build_summary(self, workflows: list[dict[str, Any]]) -> dict[str, Any]:
        scored = [workflow["score"] for workflow in workflows if workflow["score"] > 0]
        total_nodes = sum(workflow["nodes"] for workflow in workflows)
        migrated_nodes = sum(workflow["migrated"] for workflow in workflows)
        failed_nodes = sum(workflow["failed"] for workflow in workflows)
        average_score = round(sum(scored) / len(scored), 1) if scored else 0.0
        return {
            "totalWorkflows": len(workflows),
            "verifiedWorkflows": sum(1 for workflow in workflows if workflow["status"] == "verified"),
            "averageScore": average_score,
            "totalNodes": total_nodes,
            "migratedNodes": migrated_nodes,
            "failedNodes": failed_nodes,
            "pendingReviews": sum(1 for item in self._review_queue if item["verdict"] is None),
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

    def _require_workflow(self, workflow_id: str) -> None:
        if not any(item["id"] == workflow_id for item in self._workflows):
            raise LookupError(f"Unknown workflow: {workflow_id}")
