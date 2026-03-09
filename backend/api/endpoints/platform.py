"""Platform connection endpoints — connect to Coze/Dify via API or DB."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# ── Request / Response models ────────────────────────────────


class CozeConnectRequest(BaseModel):
    access_token: str
    api_base: str = "https://api.coze.com"


class DifyConnectRequest(BaseModel):
    api_base: str
    api_key: str


class DbConnectRequest(BaseModel):
    platform: str  # "coze" | "dify"
    db_url: str


class CozeWorkflowFetchRequest(BaseModel):
    access_token: str
    api_base: str = "https://api.coze.com"
    space_id: str


class CozeWorkflowSelectRequest(BaseModel):
    access_token: str
    api_base: str = "https://api.coze.com"
    workflow_id: str


# ── Coze endpoints ───────────────────────────────────────────


@router.post("/coze/connect")
async def coze_connect(req: CozeConnectRequest):
    """Test Coze PAT credentials and return workspace list."""
    from core.coze.api_client import CozeApiClient

    client = CozeApiClient(access_token=req.access_token, base_url=req.api_base)
    result = await client.test_connection()
    if not result.get("connected"):
        raise HTTPException(status_code=401, detail=result.get("error", "Connection failed"))
    # Also fetch spaces for the response
    spaces = await client.list_spaces()
    return {"connected": True, "workspaces": spaces}


@router.post("/coze/workflows")
async def coze_list_workflows(req: CozeWorkflowFetchRequest):
    """List Coze workflows in a workspace."""
    from core.coze.api_client import CozeApiClient

    client = CozeApiClient(access_token=req.access_token, base_url=req.api_base)
    bots = await client.list_workflows(req.space_id)
    return {"workflows": bots}


@router.post("/coze/workflows/fetch")
async def coze_fetch_workflow(req: CozeWorkflowSelectRequest):
    """Fetch a single Coze workflow and return raw data."""
    from core.coze.api_client import CozeApiClient

    client = CozeApiClient(access_token=req.access_token, base_url=req.api_base)
    data = await client.fetch_workflow(req.workflow_id)
    return {"workflow": data}


# ── Dify endpoints ───────────────────────────────────────────


@router.post("/dify/connect")
async def dify_connect(req: DifyConnectRequest):
    """Test Dify API/console credentials."""
    from core.dify.api_client import DifyApiClient

    client = DifyApiClient(api_base=req.api_base, api_key=req.api_key)
    result = await client.test_connection()
    if not result.get("connected"):
        raise HTTPException(status_code=401, detail=result.get("error", "Connection failed"))
    return result


@router.post("/dify/apps")
async def dify_list_apps(req: DifyConnectRequest):
    """List Dify apps/workflows via console API."""
    from core.dify.api_client import DifyApiClient

    client = DifyApiClient(api_base=req.api_base, api_key=req.api_key)
    apps = await client.list_apps()
    return {"apps": apps}


# ── Database direct connection ───────────────────────────────


@router.post("/db/connect")
async def db_connect(req: DbConnectRequest):
    """Test a direct database connection to Coze or Dify."""
    if req.platform == "dify":
        from core.dify.db_reader import DifyDbReader

        reader = DifyDbReader(req.db_url)
        ok = reader.test_connection()
        return {"connected": ok, "platform": "dify"}
    elif req.platform == "coze":
        from core.coze.db_reader import CozeDbReader

        reader = CozeDbReader(req.db_url)
        ok = reader.test_connection()
        return {"connected": ok, "platform": "coze"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {req.platform}")


@router.post("/db/workflows")
async def db_list_workflows(req: DbConnectRequest):
    """List workflows from a database."""
    if req.platform == "dify":
        from core.dify.db_reader import DifyDbReader

        reader = DifyDbReader(req.db_url)
        apps = reader.list_apps()
        return {"workflows": apps}
    elif req.platform == "coze":
        from core.coze.db_reader import CozeDbReader

        reader = CozeDbReader(req.db_url)
        workflows = reader.list_workflows()
        return {"workflows": workflows}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {req.platform}")
