from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.workbench.service import WorkbenchService
from db.database import get_db

router = APIRouter()
service = WorkbenchService()


@router.get("/overview")
async def get_workbench_overview(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return service.get_overview(db, limit=limit)
