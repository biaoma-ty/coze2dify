from __future__ import annotations

import hashlib
import json
from typing import Any


class DiffDetector:
    """Detects changes between source and target workflows."""

    @staticmethod
    def compute_hash(workflow_data: dict[str, Any]) -> str:
        serialized = json.dumps(workflow_data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def detect_changes(
        self,
        source_workflows: dict[str, dict],
        target_workflows: dict[str, dict],
    ) -> tuple[list[str], list[str], list[str]]:
        """Returns (new_ids, updated_ids, deleted_ids)."""
        source_ids = set(source_workflows.keys())
        target_ids = set(target_workflows.keys())

        new_ids = list(source_ids - target_ids)
        deleted_ids = list(target_ids - source_ids)

        updated_ids = []
        for wf_id in source_ids & target_ids:
            source_hash = self.compute_hash(source_workflows[wf_id])
            target_hash = self.compute_hash(target_workflows[wf_id])
            if source_hash != target_hash:
                updated_ids.append(wf_id)

        return new_ids, updated_ids, deleted_ids
