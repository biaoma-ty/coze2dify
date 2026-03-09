from __future__ import annotations

from typing import Any, Callable

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class SyncScheduler:
    """Manages scheduled sync tasks."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(
            daemon=True,
            timezone="UTC",
            job_defaults={"coalesce": True, "max_instances": 1},
        )
        self._scheduler.start()

    def schedule(self, config_id: str, cron_expression: str, callback: Callable[[], None]) -> dict[str, Any]:
        trigger = CronTrigger.from_crontab(cron_expression, timezone="UTC")
        job = self._scheduler.add_job(
            callback,
            trigger=trigger,
            id=self._job_id(config_id),
            name=f"sync:{config_id}",
            replace_existing=True,
        )
        return self._serialize_job(job, config_id, cron_expression)

    def cancel(self, config_id: str) -> bool:
        job_id = self._job_id(config_id)
        job = self._scheduler.get_job(job_id)
        if job is None:
            return False
        self._scheduler.remove_job(job_id)
        return True

    def get_job(self, config_id: str) -> dict[str, Any] | None:
        job = self._scheduler.get_job(self._job_id(config_id))
        if job is None:
            return None
        return self._serialize_job(job, config_id)

    def get_jobs(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        for job in self._scheduler.get_jobs():
            config_id = job.id.removeprefix("sync-config-")
            jobs.append(self._serialize_job(job, config_id))
        return jobs

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    @staticmethod
    def _job_id(config_id: str) -> str:
        return f"sync-config-{config_id}"

    @staticmethod
    def _serialize_job(job: Job, config_id: str, cron_expression: str | None = None) -> dict[str, Any]:
        resolved_config_id: int | str = int(config_id) if str(config_id).isdigit() else config_id
        return {
            "config_id": resolved_config_id,
            "job_id": job.id,
            "cron_expression": cron_expression or str(job.trigger),
            "next_run_at": job.next_run_time.isoformat() if job.next_run_time else None,
        }
