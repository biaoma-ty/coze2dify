from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SyncConfigRequest(BaseModel):
    name: str
    coze_db_type: str = "postgresql"
    coze_db_url: str
    dify_db_url: str
    sync_mode: str = "manual"
    cron_expression: str | None = None


class ConflictResolveRequest(BaseModel):
    strategy: str = "source_wins"


@router.post("/config")
async def create_sync_config(req: SyncConfigRequest):
    # TODO: Save to DB
    return {"status": "created", "config": req.model_dump()}


@router.get("/config")
async def get_sync_config():
    return {"config": None}


@router.post("/config/test")
async def test_connections(req: SyncConfigRequest):
    return {"coze_db": "not_tested", "dify_db": "not_tested"}


@router.post("/execute")
async def execute_sync():
    # TODO: Trigger sync engine
    return {"status": "not_implemented"}


@router.get("/status")
async def get_sync_status():
    return {"status": "idle"}


@router.get("/history")
async def get_sync_history():
    return {"history": []}


@router.get("/history/{history_id}")
async def get_sync_detail(history_id: str):
    return {"detail": None}


@router.post("/schedule")
async def set_schedule(cron_expression: str):
    return {"status": "not_implemented"}


@router.delete("/schedule")
async def cancel_schedule():
    return {"status": "not_implemented"}


@router.post("/diff")
async def preview_diff():
    return {"new": 0, "updated": 0, "conflicts": 0}


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, req: ConflictResolveRequest):
    return {"status": "not_implemented"}
