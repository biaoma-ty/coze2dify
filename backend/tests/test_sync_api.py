from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import main
from api.endpoints import sync as sync_endpoints
from api.router import api_router
from core.sync.conflict_resolver import ConflictStrategy
from core.sync.scheduler import SyncScheduler
from core.sync.sync_engine import SyncEngine
from db.database import Base, get_db
from db.models import MigrationTask, SyncConfig, SyncHistory


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FakeCozeReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def test_connection(self) -> bool:
        return True

    def list_workflows(self) -> list[dict[str, str]]:
        return [{"id": "wf-api", "name": "API Flow"}]


class FakeDifyReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def test_connection(self) -> bool:
        return True

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
            "status": "succeeded",
            "target": {
                "scheme": "postgresql",
                "host": "dify.test",
                "port": None,
                "database": "app",
                "display_url": "postgresql://***@dify.test/app",
            },
        }
        snapshot["audit"] = {
            "source": {
                "type": "database",
                "workflow_id": task.source_workflow_id,
                "workflow_name": task.source_workflow_name,
            },
            "last_write": snapshot["write_result"],
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
    monkeypatch.setattr(sync_endpoints, "CozeDbReader", FakeCozeReader)
    monkeypatch.setattr(sync_endpoints, "DifyDbReader", FakeDifyReader)

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
    config_payload = config_response.json()["config"]
    assert config_payload["coze_db"]["display_url"] == "postgresql://***@coze.test/app"
    assert config_payload["dify_db"]["display_url"] == "postgresql://***@dify.test/app"
    assert config_payload["has_stored_coze_db_url"] is True
    assert config_payload["has_stored_dify_db_url"] is True

    test_response = client.post(
        "/api/v1/sync/config/test",
        json={
            "config_id": config_payload["id"],
            "name": "Manual Sync",
            "coze_db_url": "",
            "dify_db_url": "",
        },
    )
    assert test_response.status_code == 200
    assert test_response.json()["coze_db"]["connected"] is True

    with session_factory() as db:
        histories = db.execute(select(SyncHistory)).scalars().all()
        tasks = db.execute(select(MigrationTask)).scalars().all()

    assert len(histories) == 1
    assert histories[0].workflows_synced == 1
    assert histories[0].conflicts_resolved["audit"]["source_db"]["display_url"] == "postgresql://***@coze.test/app"
    assert histories[0].conflicts_resolved["audit"]["target_db"]["display_url"] == "postgresql://***@dify.test/app"
    assert len(tasks) == 1
    assert tasks[0].sync_config_id == histories[0].sync_config_id


def test_sync_schedule_diff_and_conflict_endpoints_are_wired(tmp_path, monkeypatch) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-api-extra.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    def override_get_db():
        with session_factory() as db:
            yield db

    class StubSyncEngine:
        def preview_diff(self, db, config):
            return {
                "config_id": config.id,
                "status": "partial",
                "summary": {
                    "created": 1,
                    "updated": 0,
                    "failed": 0,
                    "skipped": 0,
                    "unsupported": 0,
                    "conflicts": 1,
                },
                "items": [
                    {
                        "action": "create",
                        "status": "created",
                        "source_workflow_id": "wf-create",
                        "source_workflow_name": "Create Flow",
                        "target_app_id": None,
                        "conversion_id": None,
                        "message": "Will create on next sync.",
                    }
                ],
            }

        def resolve_conflict(self, db, history, *, conflict_id: str, strategy: ConflictStrategy):
            payload = dict(history.conflicts_resolved)
            summary = dict(payload["summary"])
            item = dict(payload["items"][0])
            item["status"] = "skipped"
            item["action"] = "keep"
            item["resolution"] = {
                "strategy": strategy.value,
                "status": "kept_target",
            }
            summary["conflicts"] = 0
            summary["skipped"] = 1
            history.conflicts_count = 0
            history.status = "completed"
            history.conflicts_resolved = {
                "summary": summary,
                "items": [item],
            }
            db.add(history)
            db.commit()
            db.refresh(history)
            return {
                "id": str(history.id),
                "sync_config_id": history.sync_config_id,
                "sync_config_name": history.sync_config.name if history.sync_config else None,
                "trigger_type": history.trigger_type,
                "status": history.status,
                "started_at": history.started_at.isoformat() if history.started_at else None,
                "completed_at": history.completed_at.isoformat() if history.completed_at else None,
                "workflows_synced": history.workflows_synced,
                "workflows_failed": history.workflows_failed,
                "conflicts_count": history.conflicts_count,
                "summary": history.conflicts_resolved["summary"],
                "items": history.conflicts_resolved["items"],
            }

        def execute_sync(self, db, config, *, trigger_type: str = "manual"):
            return {"id": "unused", "status": "completed"}

    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_get_db

    scheduler = SyncScheduler()
    monkeypatch.setattr(sync_endpoints, "sync_engine", StubSyncEngine())
    monkeypatch.setattr(sync_endpoints, "sync_scheduler", scheduler)

    client = TestClient(app)
    schedule_payload = {
        "name": "Nightly Sync",
        "coze_db_url": "postgresql://coze.test/app",
        "dify_db_url": "postgresql://dify.test/app",
        "cron_expression": "0 3 * * *",
    }

    schedule_response = client.post("/api/v1/sync/schedule", json=schedule_payload)
    assert schedule_response.status_code == 200
    schedule_data = schedule_response.json()
    config_id = schedule_data["config"]["id"]
    assert schedule_data["config"]["sync_mode"] == "scheduled"
    assert schedule_data["schedule"]["config_id"] == config_id

    diff_response = client.post(
        "/api/v1/sync/diff",
        json={
            "config_id": config_id,
            "name": "Nightly Sync",
            "coze_db_url": "postgresql://coze.test/app",
            "dify_db_url": "postgresql://dify.test/app",
        },
    )
    assert diff_response.status_code == 200
    assert diff_response.json()["summary"]["created"] == 1

    with session_factory() as db:
        config = db.get(SyncConfig, config_id)
        history = SyncHistory(
            sync_config_id=config_id,
            trigger_type="manual",
            status="partial",
            conflicts_count=1,
            conflicts_resolved={
                "summary": {
                    "created": 0,
                    "updated": 0,
                    "failed": 0,
                    "skipped": 0,
                    "unsupported": 0,
                    "conflicts": 1,
                },
                "items": [
                    {
                        "action": "update",
                        "status": "conflict",
                        "source_workflow_id": "wf-conflict",
                        "source_workflow_name": "Conflict Flow",
                        "target_app_id": "app-existing",
                        "conversion_id": None,
                        "message": "Resolve me.",
                    }
                ],
            },
            started_at=_utcnow(),
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        history_id = history.id
        assert config is not None

    conflict_response = client.post(
        "/api/v1/sync/conflicts/wf-conflict/resolve",
        json={"history_id": str(history_id), "strategy": "target_wins"},
    )
    assert conflict_response.status_code == 200
    assert conflict_response.json()["items"][0]["status"] == "skipped"

    status_response = client.get("/api/v1/sync/status")
    assert status_response.status_code == 200
    assert status_response.json()["scheduled_jobs"][0]["config_id"] == config_id

    cancel_response = client.delete(f"/api/v1/sync/schedule?config_id={config_id}")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["cancelled"] is True
    assert cancel_response.json()["config"]["enabled"] is False

    scheduler.shutdown()


def test_restore_schedules_registers_only_enabled_scheduled_configs(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-restore.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    scheduler = SyncScheduler()

    try:
        with session_factory() as db:
            db.add_all(
                [
                    SyncConfig(
                        name="Enabled Schedule",
                        coze_db_url="postgresql://coze.test/enabled",
                        dify_db_url="postgresql://dify.test/enabled",
                        sync_mode="scheduled",
                        cron_expression="0 3 * * *",
                        enabled=True,
                    ),
                    SyncConfig(
                        name="Disabled Schedule",
                        coze_db_url="postgresql://coze.test/disabled",
                        dify_db_url="postgresql://dify.test/disabled",
                        sync_mode="scheduled",
                        cron_expression="15 4 * * *",
                        enabled=False,
                    ),
                    SyncConfig(
                        name="Manual Config",
                        coze_db_url="postgresql://coze.test/manual",
                        dify_db_url="postgresql://dify.test/manual",
                        sync_mode="manual",
                        cron_expression=None,
                        enabled=True,
                    ),
                    SyncConfig(
                        name="Missing Cron",
                        coze_db_url="postgresql://coze.test/nocron",
                        dify_db_url="postgresql://dify.test/nocron",
                        sync_mode="scheduled",
                        cron_expression=None,
                        enabled=True,
                    ),
                ]
            )
            db.commit()

        restored_jobs = sync_endpoints.restore_schedules(session_factory=session_factory, scheduler=scheduler)
        scheduled_jobs = scheduler.get_jobs()
    finally:
        scheduler.shutdown()

    assert len(restored_jobs) == 1
    assert len(scheduled_jobs) == 1
    assert restored_jobs[0]["config_id"] == scheduled_jobs[0]["config_id"]
    assert restored_jobs[0]["cron_expression"] == "0 3 * * *"


def test_app_startup_invokes_schedule_restore(monkeypatch) -> None:
    called = {"create_all": 0, "restore_schedules": 0}

    def fake_create_all(*args, **kwargs) -> None:  # noqa: ANN002, ANN003 - test double
        called["create_all"] += 1

    def fake_restore_schedules() -> list[dict[str, object]]:
        called["restore_schedules"] += 1
        return []

    monkeypatch.setattr(main.Base.metadata, "create_all", fake_create_all)
    monkeypatch.setattr(main.sync_endpoints, "restore_schedules", fake_restore_schedules)

    main.ensure_project_tables()

    assert called == {"create_all": 1, "restore_schedules": 1}
