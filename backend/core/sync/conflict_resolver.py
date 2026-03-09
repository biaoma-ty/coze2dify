from __future__ import annotations

from enum import Enum
from typing import Any


class ConflictStrategy(str, Enum):
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    MANUAL = "manual"


class ConflictResolver:
    """Resolves conflicts when both source and target have changed."""

    def resolve(
        self,
        workflow_id: str,
        source_data: dict[str, Any],
        target_data: dict[str, Any],
        strategy: ConflictStrategy = ConflictStrategy.MANUAL,
    ) -> dict[str, Any] | None:
        if strategy == ConflictStrategy.SOURCE_WINS:
            return dict(source_data)
        if strategy == ConflictStrategy.TARGET_WINS:
            return None  # Skip, keep target
        return None  # Manual: needs user intervention
