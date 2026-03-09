from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from core.coze.parser import CozeParser

router = APIRouter()


class CozeApiRequest(BaseModel):
    access_token: str
    workflow_id: str


class DbConnectRequest(BaseModel):
    db_type: str = "postgresql"
    db_url: str


@router.post("/upload")
async def upload_coze_workflow(file: UploadFile = File(...)):
    content = await file.read()
    fmt = "yaml" if file.filename and file.filename.endswith((".yaml", ".yml")) else "json"
    parser = CozeParser()
    ir_workflow = parser.parse_file(content, fmt)
    return {
        "workflow_id": ir_workflow.id,
        "node_count": len(ir_workflow.nodes),
        "edge_count": len(ir_workflow.edges),
        "nodes": [{"id": n.id, "type": n.source_type_name, "title": n.title} for n in ir_workflow.nodes],
    }


@router.post("/fetch")
async def fetch_from_api(req: CozeApiRequest):
    # TODO: Implement via CozeApiClient
    return {"status": "not_implemented", "message": "Coze API fetch not yet implemented"}


@router.post("/db/connect")
async def test_db_connection(req: DbConnectRequest):
    # TODO: Test database connection
    return {"status": "not_implemented"}


@router.get("/db/workflows")
async def list_db_workflows():
    # TODO: List workflows from Coze DB
    return {"workflows": []}


@router.post("/db/fetch")
async def fetch_from_db(workflow_id: str):
    # TODO: Read workflow from Coze DB
    return {"status": "not_implemented"}
