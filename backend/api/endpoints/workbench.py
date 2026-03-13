from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.workbench.service import WorkbenchService

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
async def get_workbench_overview(limit: int = Query(default=50, ge=1, le=200)):
    return service.get_overview(limit=limit)


@router.post("/batch-migrate")
async def batch_migrate_workflows():
    return service.batch_migrate()


@router.get("/workflows/{workflow_id}/topology")
async def get_workflow_topology(workflow_id: str):
    try:
        return service.get_topology(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/equivalence")
async def get_workflow_equivalence(workflow_id: str):
    try:
        return service.get_equivalence(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/tests")
async def get_workflow_tests(workflow_id: str):
    try:
        return service.get_tests(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/tests/generate")
async def generate_workflow_tests(workflow_id: str):
    try:
        return service.generate_tests(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/tests/run")
async def run_workflow_tests(workflow_id: str):
    try:
        return service.run_tests(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/knowledge")
async def get_workflow_knowledge(workflow_id: str):
    try:
        return service.get_knowledge(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/review")
async def get_workflow_review(workflow_id: str):
    try:
        return service.get_review_queue(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/review/{review_id}")
async def update_review_verdict(workflow_id: str, review_id: str, req: ReviewVerdictRequest):
    try:
        return service.update_review_verdict(workflow_id, review_id, req.verdict)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/release")
async def get_workflow_release(workflow_id: str):
    try:
        return service.get_release(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/release/traffic")
async def update_workflow_traffic(workflow_id: str, req: TrafficRequest):
    try:
        return service.update_traffic(workflow_id, req.traffic)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/release/rollback")
async def rollback_workflow_release(workflow_id: str, req: RollbackRequest):
    try:
        return service.rollback_release(workflow_id, req.version)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/sandbox")
async def get_workflow_sandbox(workflow_id: str):
    try:
        return service.get_sandbox(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/sandbox/start")
async def start_workflow_sandbox(workflow_id: str):
    try:
        return service.start_sandbox(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/sandbox/stop")
async def stop_workflow_sandbox(workflow_id: str):
    try:
        return service.stop_sandbox(workflow_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/sandbox/messages")
async def send_workflow_sandbox_message(workflow_id: str, req: SandboxMessageRequest):
    try:
        return service.send_sandbox_message(workflow_id, req.text)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
