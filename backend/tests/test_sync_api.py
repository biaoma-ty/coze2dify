from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from api.endpoints import sync as sync_endpoints
from api.router import api_router
from core.sync.sync_engine import SyncEngine
from db.database import Base, get_db
from db.models import MigrationTask, SyncHistory


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FakeCozeReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_workflows(self) -> list[dict[str, str]]:
        return [{"id": "wf-api", "name": "API Flow"}]


class FakeDifyReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_apps(self) -> list[dict[str, str]]:
        return []

    def read_workflow(self, app_id: str) -> dict[str, object] | None:
        return None


class FakeConversionService:
    def convert_from_db(self, db, *, db_url: str, workflow_id: str) -> dict[str, object]:
        dsl_payload = {
            "workflow": {
                "graph": {"nodes": [{"id": workflow_id}], "edges": []},
                "features": {"mode": workflow_id},
            }
        }
        task = MigrationTask(
            source_type="database",
            source_workflow_id=workflow_id,
            source_workflow_name="API Flow",
            status="converted",
            ir_snapshot={"dify_dsl": dsl_payload, "write_result": None},
            dify_dsl="workflow: {}\n",
            report={"workflow_name": workflow_id, "total_nodes": 1},
            completed_at=_utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {
            "conversion_id": str(task.id),
            "dsl": dsl_payload,
            "report": task.report,
            "status": task.status,
        }

    def write_to_dify(
        self,
        db,
        conversion_id: str,
        *,
        db_url: str | None = None,
        app_id: str | None = None,
    ) -> dict[str, str]:
        task = db.get(MigrationTask, int(conversion_id))
        snapshot = task.ir_snapshot or {}
        snapshot["write_result"] = {
            "app_id": app_id or "created-app",
            "mode": "update" if app_id else "create",
            "db_url": db_url,
        }
        task.ir_snapshot = snapshot
        task.status = "updated" if app_id else "written"
        task.completed_at = _utcnow()
        db.add(task)
        db.commit()
        db.refresh(task)
        return {
            "conversion_id": conversion_id,
            "app_id": snapshot["write_result"]["app_id"],
            "mode": snapshot["write_result"]["mode"],
            "status": task.status,
        }


def test_sync_execute_endpoint_persists_history_and_exposes_detail(tmp_path, monkeypatch) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-api.db'}",
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

    monkeypatch.setattr(
        sync_endpoints,
        "sync_engine",
        SyncEngine(
            FakeConversionService(),
            coze_reader_factory=FakeCozeReader,
            dify_reader_factory=FakeDifyReader,
        ),
    )

    client = TestClient(app)
    payload = {
        "name": "Manual Sync",
        "coze_db_url": "postgresql://coze.test/app",
        "dify_db_url": "postgresql://dify.test/app",
    }

    execute_response = client.post("/api/v1/sync/execute", json=payload)
    assert execute_response.status_code == 200
    execute_data = execute_response.json()
    assert execute_data["summary"] == {
        "created": 1,
        "updated": 0,
        "failed": 0,
        "skipped": 0,
        "unsupported": 0,
        "conflicts": 0,
    }
    assert execute_data["items"][0]["status"] == "created"
    assert execute_data["items"][0]["target_app_id"] == "created-app"

    history_response = client.get("/api/v1/sync/history")
    assert history_response.status_code == 200
    history = history_response.json()["history"]
    assert len(history) == 1
    assert history[0]["id"] == execute_data["id"]
    assert history[0]["summary"]["created"] == 1

    detail_response = client.get(f"/api/v1/sync/history/{execute_data['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["items"][0]["source_workflow_id"] == "wf-api"

    config_response = client.get("/api/v1/sync/config")
    assert config_response.status_code == 200
    assert config_response.json()["config"]["coze_db_url"] == payload["coze_db_url"]

    with session_factory() as db:
        histories = db.execute(select(SyncHistory)).scalars().all()
        tasks = db.execute(select(MigrationTask)).scalars().all()

    assert len(histories) == 1
    assert histories[0].workflows_synced == 1
    assert len(tasks) == 1
    assert tasks[0].sync_config_id == histories[0].sync_config_id
