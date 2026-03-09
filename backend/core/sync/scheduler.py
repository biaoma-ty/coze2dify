from __future__ import annotations

from typing import Any, Callable


class SyncScheduler:
    """Manages scheduled sync tasks."""

    def __init__(self) -> None:
        self._jobs: dict[str, Any] = {}

    def schedule(self, config_id: str, cron_expression: str, callback: Callable) -> None:
        # TODO: Integrate APScheduler
        self._jobs[config_id] = {"cron": cron_expression, "callback": callback}

    def cancel(self, config_id: str) -> None:
        self._jobs.pop(config_id, None)

    def get_jobs(self) -> dict[str, Any]:
        return self._jobs.copy()
