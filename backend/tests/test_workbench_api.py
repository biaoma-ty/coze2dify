from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.router import api_router
from db.database import Base, get_db
from db.models import MigrationTask, SyncConfig


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_workbench_overview_aggregates_real_conversion_history(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-workbench-overview.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    def override_get_db():
        with session_factory() as db:
            yield db

    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    with session_factory() as db:
        sync_config = SyncConfig(
            name="Nightly Sync",
            coze_db_url="postgresql://coze.example/app",
            dify_db_url="postgresql://dify.example/app",
        )
        db.add(sync_config)
        db.flush()

        db.add_all(
            [
                MigrationTask(
                    source_type="database",
                    source_workflow_id="wf-sync",
                    source_workflow_name="Sync Workflow",
                    sync_config_id=sync_config.id,
                    status="converted",
                    ir_snapshot={},
                    report={
                        "workflow_name": "Sync Workflow",
                        "supported": True,
                        "total_nodes": 4,
                        "mapped_count": 4,
                        "partial_count": 0,
                        "skipped_count": 0,
                    },
                    completed_at=_utcnow(),
                ),
                MigrationTask(
                    source_type="upload",
                    source_workflow_id="wf-alpha",
                    source_workflow_name="Alpha Flow",
                    status="written",
                    ir_snapshot={
                        "write_result": {
                            "app_id": "app-alpha",
                            "status": "succeeded",
                        }
                    },
                    report={
                        "workflow_name": "Alpha Flow",
                        "supported": True,
                        "requires_manual_review": False,
                        "total_nodes": 10,
                        "mapped_count": 8,
                        "partial_count": 1,
                        "skipped_count": 0,
                    },
                    completed_at=datetime(2026, 3, 12, 10, 0, 0),
                ),
                MigrationTask(
                    source_type="api",
                    source_workflow_id="wf-beta",
                    source_workflow_name="Beta Flow",
                    status="converted",
                    ir_snapshot={},
                    report={
                        "workflow_name": "Beta Flow",
                        "supported": True,
                        "requires_manual_review": True,
                        "total_nodes": 8,
                        "mapped_count": 6,
                        "partial_count": 1,
                        "skipped_count": 0,
                    },
                    completed_at=datetime(2026, 3, 12, 9, 0, 0),
                ),
                MigrationTask(
                    source_type="database",
                    source_workflow_id="wf-gamma",
                    source_workflow_name="Gamma Flow",
                    status="blocked",
                    ir_snapshot={},
                    report={
                        "workflow_name": "Gamma Flow",
                        "supported": False,
                        "requires_manual_review": False,
                        "total_nodes": 6,
                        "mapped_count": 0,
                        "partial_count": 0,
                        "skipped_count": 0,
                    },
                    completed_at=datetime(2026, 3, 11, 20, 0, 0),
                ),
            ]
        )
        db.commit()

    response = client.get("/api/v1/workbench/overview?limit=10")
    assert response.status_code == 200
    payload = response.json()

    assert payload["summary"] == {
        "total_workflows": 3,
        "verified_workflows": 1,
        "average_score": 83.1,
        "total_nodes": 24,
        "migrated_nodes": 16,
        "failed_nodes": 8,
        "pending_reviews": 1,
    }

    workflows = payload["workflows"]
    assert [workflow["coze_id"] for workflow in workflows] == ["wf-alpha", "wf-beta", "wf-gamma"]

    alpha = workflows[0]
    assert alpha["dify_id"] == "app-alpha"
    assert alpha["status"] == "verified"
    assert alpha["score"] == 85.0
    assert alpha["complexity"] == "medium"

    beta = workflows[1]
    assert beta["status"] == "testing"
    assert beta["migrated"] == 7
    assert beta["failed"] == 1
    assert beta["requires_manual_review"] is True

    gamma = workflows[2]
    assert gamma["status"] == "failed"
    assert gamma["score"] == 0.0
    assert gamma["complexity"] == "low"
