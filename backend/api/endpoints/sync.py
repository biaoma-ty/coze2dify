from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.coze.db_reader import CozeDbReader
from core.dify.db_reader import DifyDbReader
from core.sync.conflict_resolver import ConflictStrategy
from core.sync.scheduler import SyncScheduler
from core.sync.sync_engine import SyncEngine
from db.database import SessionLocal, get_db
from db.models import SyncConfig, SyncHistory

router = APIRouter()
sync_engine = SyncEngine()
sync_scheduler = SyncScheduler()
logger = logging.getLogger(__name__)


class SyncConfigRequest(BaseModel):
    config_id: int | None = None
    name: str = Field(default="Manual Sync")
    coze_db_type: str = "postgresql"
    coze_db_url: str
    dify_db_url: str
    sync_mode: str = "manual"
    cron_expression: str | None = None


class SyncScheduleRequest(SyncConfigRequest):
    cron_expression: str
    sync_mode: str = "scheduled"


class ConflictResolveRequest(BaseModel):
    history_id: str
    strategy: ConflictStrategy = ConflictStrategy.SOURCE_WINS


@router.post("/config")
async def create_sync_config(
    req: SyncConfigRequest,
    db: Session = Depends(get_db),
):
    config = _upsert_sync_config(db, req)
    return {"config": _serialize_config(config)}


@router.get("/config")
async def get_sync_config(db: Session = Depends(get_db)):
    stmt = select(SyncConfig).order_by(SyncConfig.updated_at.desc(), SyncConfig.id.desc())
    config = db.execute(stmt).scalars().first()
    return {"config": _serialize_config(config) if config else None}


@router.post("/config/test")
async def test_connections(req: SyncConfigRequest):
    return {
        "coze_db": _test_connection(CozeDbReader, req.coze_db_url),
        "dify_db": _test_connection(DifyDbReader, req.dify_db_url),
    }


@router.post("/execute")
async def execute_sync(
    req: SyncConfigRequest,
    db: Session = Depends(get_db),
):
    config = _upsert_sync_config(db, req)
    return sync_engine.execute_sync(db, config, trigger_type="manual")


@router.get("/status")
async def get_sync_status(db: Session = Depends(get_db)):
    stmt = select(SyncHistory).order_by(SyncHistory.started_at.desc(), SyncHistory.id.desc())
    latest = db.execute(stmt).scalars().first()
    if latest is None:
        return {"status": "idle", "history_id": None, "scheduled_jobs": sync_scheduler.get_jobs()}
    return {"status": latest.status, "history_id": str(latest.id), "scheduled_jobs": sync_scheduler.get_jobs()}


@router.get("/history")
async def get_sync_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(SyncHistory).order_by(SyncHistory.started_at.desc(), SyncHistory.id.desc()).limit(limit)
    histories = db.execute(stmt).scalars().all()
    return {"history": [sync_engine.serialize_history(history) for history in histories]}


@router.get("/history/{history_id}")
async def get_sync_detail(
    history_id: str,
    db: Session = Depends(get_db),
):
    return sync_engine.serialize_history(_get_history(db, history_id), include_items=True)


@router.post("/schedule")
async def set_schedule(
    req: SyncScheduleRequest,
    db: Session = Depends(get_db),
):
    config = _upsert_sync_config(db, req)
    schedule = sync_scheduler.schedule(str(config.id), req.cron_expression, _scheduled_sync_callback(config.id))
    return {"config": _serialize_config(config), "schedule": schedule}


@router.delete("/schedule")
async def cancel_schedule(
    config_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    config = db.get(SyncConfig, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Sync config {config_id} not found")

    config.enabled = False
    db.add(config)
    db.commit()
    db.refresh(config)

    cancelled = sync_scheduler.cancel(str(config.id))
    return {"config": _serialize_config(config), "cancelled": cancelled}


@router.post("/diff")
async def preview_diff(
    req: SyncConfigRequest,
    db: Session = Depends(get_db),
):
    config = _upsert_sync_config(db, req)
    return sync_engine.preview_diff(db, config)


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    req: ConflictResolveRequest,
    db: Session = Depends(get_db),
):
    history = _get_history(db, req.history_id)
    try:
        return sync_engine.resolve_conflict(db, history, conflict_id=conflict_id, strategy=req.strategy)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _upsert_sync_config(db: Session, req: SyncConfigRequest) -> SyncConfig:
    config: SyncConfig | None = None

    if req.config_id is not None:
        config = db.get(SyncConfig, req.config_id)
        if config is None:
            raise HTTPException(status_code=404, detail=f"Sync config {req.config_id} not found")
    else:
        stmt = (
            select(SyncConfig)
            .where(
                SyncConfig.coze_db_url == req.coze_db_url,
                SyncConfig.dify_db_url == req.dify_db_url,
                SyncConfig.sync_mode == req.sync_mode,
            )
            .order_by(SyncConfig.updated_at.desc(), SyncConfig.id.desc())
        )
        config = db.execute(stmt).scalars().first()

    if config is None:
        config = SyncConfig(
            name=req.name.strip() or "Manual Sync",
            coze_db_type=req.coze_db_type,
            coze_db_url=req.coze_db_url,
            dify_db_url=req.dify_db_url,
            sync_mode=req.sync_mode,
            cron_expression=req.cron_expression,
            enabled=True,
        )
    else:
        config.name = req.name.strip() or config.name or "Manual Sync"
        config.coze_db_type = req.coze_db_type
        config.coze_db_url = req.coze_db_url
        config.dify_db_url = req.dify_db_url
        config.sync_mode = req.sync_mode
        config.cron_expression = req.cron_expression
        config.enabled = True

    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _serialize_config(config: SyncConfig | None) -> dict[str, str | int | bool | None] | None:
    if config is None:
        return None
    return {
        "id": config.id,
        "name": config.name,
        "coze_db_type": config.coze_db_type,
        "coze_db_url": config.coze_db_url,
        "dify_db_url": config.dify_db_url,
        "sync_mode": config.sync_mode,
        "cron_expression": config.cron_expression,
        "enabled": config.enabled,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


def _test_connection(reader_cls: type[CozeDbReader] | type[DifyDbReader], db_url: str) -> dict[str, str | bool | None]:
    try:
        connected = reader_cls(db_url).test_connection()
        return {"connected": connected, "error": None if connected else "Connection test failed"}
    except Exception as exc:  # noqa: BLE001 - return actionable UI error
        return {"connected": False, "error": str(exc)}


def _get_history(db: Session, history_id: str) -> SyncHistory:
    try:
        history_pk = int(history_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Sync history {history_id} not found") from exc

    history = db.get(SyncHistory, history_pk)
    if history is None:
        raise HTTPException(status_code=404, detail=f"Sync history {history_id} not found")
    return history


def _scheduled_sync_callback(config_id: int):
    def _run() -> None:
        with SessionLocal() as db:
            config = db.get(SyncConfig, config_id)
            if config is None or not config.enabled:
                sync_scheduler.cancel(str(config_id))
                return
            sync_engine.execute_sync(db, config, trigger_type="schedule")

    return _run


def restore_schedules(
    *, session_factory=SessionLocal, scheduler: SyncScheduler | None = None
) -> list[dict[str, object]]:
    active_scheduler = scheduler or sync_scheduler
    restored_jobs: list[dict[str, object]] = []

    with session_factory() as db:
        stmt = (
            select(SyncConfig)
            .where(
                SyncConfig.enabled.is_(True),
                SyncConfig.sync_mode == "scheduled",
            )
            .order_by(SyncConfig.updated_at.desc(), SyncConfig.id.desc())
        )
        configs = db.execute(stmt).scalars().all()

        for config in configs:
            cron_expression = (config.cron_expression or "").strip()
            if not cron_expression:
                continue

            try:
                restored_jobs.append(
                    active_scheduler.schedule(
                        str(config.id),
                        cron_expression,
                        _scheduled_sync_callback(config.id),
                    )
                )
            except ValueError:
                logger.warning("Skipping invalid persisted sync schedule for config %s", config.id)

    return restored_jobs
