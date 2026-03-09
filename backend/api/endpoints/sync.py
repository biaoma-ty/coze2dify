from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.coze.db_reader import CozeDbReader
from core.dify.db_reader import DifyDbReader
from core.sync.sync_engine import SyncEngine
from db.database import get_db
from db.models import SyncConfig, SyncHistory

router = APIRouter()
sync_engine = SyncEngine()


class SyncConfigRequest(BaseModel):
    config_id: int | None = None
    name: str = Field(default="Manual Sync")
    coze_db_type: str = "postgresql"
    coze_db_url: str
    dify_db_url: str
    sync_mode: str = "manual"
    cron_expression: str | None = None


class ConflictResolveRequest(BaseModel):
    strategy: str = "source_wins"


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
        return {"status": "idle", "history_id": None}
    return {"status": latest.status, "history_id": str(latest.id)}


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
async def set_schedule(cron_expression: str):
    raise HTTPException(
        status_code=501,
        detail="Scheduled sync is not part of the manual sync MVP.",
    )


@router.delete("/schedule")
async def cancel_schedule():
    raise HTTPException(
        status_code=501,
        detail="Scheduled sync is not part of the manual sync MVP.",
    )


@router.post("/diff")
async def preview_diff():
    raise HTTPException(
        status_code=501,
        detail="Diff preview is not part of the manual sync MVP.",
    )


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, req: ConflictResolveRequest):
    raise HTTPException(
        status_code=501,
        detail="Conflict resolution is not part of the manual sync MVP.",
    )


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
