from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.sync.sync_engine import SyncEngine
from db.database import Base
from db.models import MigrationTask, SyncConfig, SyncHistory


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FakeCozeReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_workflows(self) -> list[dict[str, str]]:
        return [
            {"id": "wf-create", "name": "Create Flow"},
            {"id": "wf-update", "name": "Update Flow"},
        ]


class FakeDifyReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_apps(self) -> list[dict[str, str]]:
        return [
            {
                "app_id": "app-existing",
                "name": "Existing Target",
                "mode": "workflow",
                "description": "",
                "created_at": "",
                "updated_at": "",
                "workflow_id": "workflow-existing",
            }
        ]

    def read_workflow(self, app_id: str) -> dict[str, object] | None:
        if app_id != "app-existing":
            return None
        return {
            "app_id": app_id,
            "graph": {"nodes": [{"id": "old-node"}], "edges": []},
            "features": {"mode": "old"},
        }


class FakeConversionService:
    def __init__(self) -> None:
        self.write_calls: list[tuple[str, str | None, str | None]] = []

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
            source_workflow_name=f"Workflow {workflow_id}",
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
        mode = "update" if app_id else "create"
        target_app_id = app_id or f"created-{conversion_id}"
        snapshot["write_result"] = {
            "app_id": target_app_id,
            "mode": mode,
            "db_url": db_url,
        }
        task.ir_snapshot = snapshot
        task.status = "updated" if mode == "update" else "written"
        task.completed_at = _utcnow()
        db.add(task)
        db.commit()
        db.refresh(task)
        self.write_calls.append((conversion_id, db_url, app_id))
        return {
            "conversion_id": conversion_id,
            "app_id": target_app_id,
            "mode": mode,
            "status": task.status,
        }


def test_execute_sync_persists_create_and_update_results(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    conversion_service = FakeConversionService()
    sync_engine = SyncEngine(
        conversion_service,
        coze_reader_factory=FakeCozeReader,
        dify_reader_factory=FakeDifyReader,
    )

    with session_factory() as db:
        config = SyncConfig(
            name="Issue 5 MVP",
            coze_db_url="postgresql://coze.test/app",
            dify_db_url="postgresql://dify.test/app",
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        existing_mapping = MigrationTask(
            sync_config_id=config.id,
            source_type="database",
            source_workflow_id="wf-update",
            source_workflow_name="Update Flow",
            status="written",
            ir_snapshot={"write_result": {"app_id": "app-existing", "mode": "create"}},
            dify_dsl="workflow: {}\n",
            report={},
            completed_at=_utcnow(),
        )
        db.add(existing_mapping)
        db.commit()

        result = sync_engine.execute_sync(db, config)

        histories = db.execute(select(SyncHistory)).scalars().all()
        synced_tasks = db.execute(
            select(MigrationTask).where(MigrationTask.sync_config_id == config.id)
        ).scalars().all()

    assert result["status"] == "completed"
    assert result["summary"] == {
        "created": 1,
        "updated": 1,
        "failed": 0,
        "skipped": 0,
        "unsupported": 0,
        "conflicts": 0,
    }
    assert len(result["items"]) == 2
    assert {item["status"] for item in result["items"]} == {"created", "updated"}
    assert len(histories) == 1
    assert histories[0].workflows_synced == 2
    assert histories[0].workflows_failed == 0
    assert histories[0].conflicts_resolved["summary"]["created"] == 1
    assert histories[0].conflicts_resolved["summary"]["updated"] == 1
    assert len(synced_tasks) == 3
    assert conversion_service.write_calls == [
        ("2", "postgresql://dify.test/app", None),
        ("3", "postgresql://dify.test/app", "app-existing"),
    ]
