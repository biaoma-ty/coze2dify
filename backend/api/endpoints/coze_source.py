from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from core.coze.api_client import CozeApiClient
from core.coze.db_reader import CozeDbReader
from core.coze.parser import CozeParser
from core.engine.conversion_service import ConversionService
from db.database import get_db

router = APIRouter()
parser = CozeParser()
conversion_service = ConversionService()


class CozeApiRequest(BaseModel):
    access_token: str
    workflow_id: str
    api_base: str = "https://api.coze.com"


class DbConnectRequest(BaseModel):
    db_url: str


class DbFetchRequest(BaseModel):
    db_url: str
    workflow_id: str


@router.post("/upload")
async def upload_coze_workflow(file: UploadFile = File(...)):
    content = await file.read()
    size_limit = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > size_limit:
        raise HTTPException(status_code=413, detail=f"Upload exceeds {settings.max_upload_size_mb} MB limit")
    fmt = "yaml" if file.filename and file.filename.endswith((".yaml", ".yml")) else "json"
    ir_workflow = parser.parse_file(content, fmt)
    return {
        "workflow_id": ir_workflow.id,
        "node_count": len(ir_workflow.nodes),
        "edge_count": len(ir_workflow.edges),
        "nodes": [{"id": n.id, "type": n.source_type_name, "title": n.title} for n in ir_workflow.nodes],
    }


@router.post("/fetch")
async def fetch_from_api(req: CozeApiRequest):
    client = CozeApiClient(access_token=req.access_token, base_url=req.api_base)
    try:
        payload = await client.fetch_workflow(req.workflow_id)
        canvas = conversion_service._extract_canvas(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ir_workflow = parser.parse_dict(canvas)
    return {
        "workflow_id": req.workflow_id,
        "node_count": len(ir_workflow.nodes),
        "edge_count": len(ir_workflow.edges),
        "nodes": [{"id": n.id, "type": n.source_type_name, "title": n.title} for n in ir_workflow.nodes],
    }


@router.post("/db/connect")
def test_db_connection(req: DbConnectRequest):
    reader = CozeDbReader(req.db_url)
    return {"connected": reader.test_connection()}


@router.post("/db/workflows")
def list_db_workflows(req: DbConnectRequest):
    reader = CozeDbReader(req.db_url)
    try:
        return {"workflows": reader.list_workflows()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/db/fetch")
def fetch_from_db(req: DbFetchRequest, db: Session = Depends(get_db)):
    try:
        conversion = conversion_service.convert_from_db(db, db_url=req.db_url, workflow_id=req.workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return conversion
