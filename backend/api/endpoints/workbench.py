from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.workbench.service import WorkbenchService
from db.database import get_db

router = APIRouter()
service = WorkbenchService()


class ReviewVerdictRequest(BaseModel):
    verdict: Literal["equivalent", "acceptable", "not_eq"]


class TrafficRequest(BaseModel):
    traffic: int = Field(ge=0, le=100)


class RollbackRequest(BaseModel):
    version: str | None = None


class SandboxMessageRequest(BaseModel):
    text: str


@router.get("/overview")
def get_workbench_overview(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return service.get_overview(db, limit=limit)


@router.post("/batch-migrate")
def batch_migrate_workflows(db: Session = Depends(get_db)):
    return service.batch_migrate(db)


@router.get("/workflows/{workflow_id}/topology")
def get_workflow_topology(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_topology(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/equivalence")
def get_workflow_equivalence(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_equivalence(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/tests")
def get_workflow_tests(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_tests(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/tests/generate")
def generate_workflow_tests(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.generate_tests(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/tests/run")
def run_workflow_tests(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.run_tests(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/knowledge")
def get_workflow_knowledge(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_knowledge(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/review")
def get_workflow_review(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_review_queue(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/review/{review_id}")
def update_review_verdict(
    workflow_id: str,
    review_id: str,
    req: ReviewVerdictRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.update_review_verdict(workflow_id, review_id, req.verdict, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/release")
def get_workflow_release(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_release(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/release/traffic")
def update_workflow_traffic(
    workflow_id: str,
    req: TrafficRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.update_traffic(workflow_id, req.traffic, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/release/rollback")
def rollback_workflow_release(
    workflow_id: str,
    req: RollbackRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.rollback_release(workflow_id, req.version, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/sandbox")
def get_workflow_sandbox(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_sandbox(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/sandbox/start")
def start_workflow_sandbox(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.start_sandbox(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/sandbox/stop")
def stop_workflow_sandbox(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return service.stop_sandbox(workflow_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/sandbox/messages")
def send_workflow_sandbox_message(
    workflow_id: str,
    req: SandboxMessageRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.send_sandbox_message(workflow_id, req.text, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
