from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from fastapi.responses import Response
from sqlalchemy.orm import Session

from config import settings
from core.engine.conversion_service import ConversionService
from db.database import get_db

router = APIRouter()
service = ConversionService()


class ApiConversionRequest(BaseModel):
    access_token: str
    workflow_id: str
    api_base: str = "https://api.coze.com"


class DbConversionRequest(BaseModel):
    db_url: str
    workflow_id: str


class WriteToDifyRequest(BaseModel):
    db_url: str | None = None
    app_id: str | None = None
    confirm_reviewed: bool = False


@router.get("")
def list_conversions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_conversions(db, limit=limit, offset=offset)


@router.post("")
async def convert_workflow(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    _ensure_upload_size(content)
    try:
        conversion = service.convert_uploaded_file(db, content, file.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"conversion_id": conversion["conversion_id"], "report": conversion["report"]}


@router.post("/from-api")
async def convert_workflow_from_api(
    req: ApiConversionRequest,
    db: Session = Depends(get_db),
):
    try:
        conversion = await service.convert_from_api(
            db,
            access_token=req.access_token,
            workflow_id=req.workflow_id,
            api_base=req.api_base,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"conversion_id": conversion["conversion_id"], "report": conversion["report"]}


@router.post("/from-db")
def convert_workflow_from_db(
    req: DbConversionRequest,
    db: Session = Depends(get_db),
):
    try:
        conversion = service.convert_from_db(db, db_url=req.db_url, workflow_id=req.workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"conversion_id": conversion["conversion_id"], "report": conversion["report"]}


@router.get("/{conversion_id}")
def get_conversion(
    conversion_id: str,
    db: Session = Depends(get_db),
):
    try:
        return service.get_conversion(db, conversion_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{conversion_id}/dsl")
def download_dsl(
    conversion_id: str,
    db: Session = Depends(get_db),
):
    try:
        yaml_output = service.get_yaml(db, conversion_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=yaml_output,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f"attachment; filename=workflow_{conversion_id}.yml"},
    )


@router.get("/{conversion_id}/report")
def get_report(
    conversion_id: str,
    db: Session = Depends(get_db),
):
    try:
        return service.get_conversion(db, conversion_id)["report"]
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{conversion_id}/write-to-dify")
def write_to_dify(
    conversion_id: str,
    req: WriteToDifyRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.write_to_dify(
            db,
            conversion_id,
            db_url=req.db_url,
            app_id=req.app_id,
            confirm_reviewed=req.confirm_reviewed,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _ensure_upload_size(content: bytes) -> None:
    size_limit = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > size_limit:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds {settings.max_upload_size_mb} MB limit",
        )
