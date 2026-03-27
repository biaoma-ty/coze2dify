from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.workbench.overview_provider import WorkbenchOverviewProvider
from db.database import Base
from db.models import MigrationTask, SyncConfig


def _make_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-workbench-provider.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _seed_persisted_overview(db: Session) -> None:
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
                completed_at=datetime(2026, 3, 12, 7, 0, 0),
            ),
            MigrationTask(
                source_type="upload",
                source_workflow_id="wf-alpha",
                source_workflow_name="Alpha Flow",
                status="written",
                ir_snapshot={"write_result": {"app_id": "app-alpha", "status": "succeeded"}},
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
        ]
    )
    db.commit()


def test_overview_provider_returns_isolated_demo_snapshots() -> None:
    provider = WorkbenchOverviewProvider()

    first = provider.load_demo_workflows(limit=2)
    second = provider.load_demo_workflows(limit=2)

    first[0]["status"] = "testing"
    assert second[0]["status"] == "migrated"
    assert len(second) == 2


def test_overview_provider_loads_only_non_sync_persisted_workflows(tmp_path) -> None:
    provider = WorkbenchOverviewProvider()
    session_factory = _make_session_factory(tmp_path)
    with session_factory() as db:
        _seed_persisted_overview(db)

        assert provider.has_persisted_workflows(db) is True

        workflows = provider.load_persisted_workflows(db, limit=10)

    assert [workflow["id"] for workflow in workflows] == ["wf-alpha", "wf-beta"]
    assert workflows[0]["status"] == "verified"
    assert workflows[0]["complexity"] == "medium"
    assert workflows[1]["status"] == "testing"
    assert workflows[1]["requiresManualReview"] is True


def test_overview_provider_can_find_persisted_workflows_by_source_id_or_task_id(tmp_path) -> None:
    provider = WorkbenchOverviewProvider()
    session_factory = _make_session_factory(tmp_path)
    with session_factory() as db:
        task = MigrationTask(
            source_type="upload",
            source_workflow_id="wf-detached",
            source_workflow_name="Detached Flow",
            status="pending",
            ir_snapshot={},
            report={
                "workflow_name": "Detached Flow",
                "supported": True,
                "total_nodes": 3,
                "mapped_count": 0,
                "partial_count": 0,
                "skipped_count": 0,
            },
            completed_at=datetime(2026, 3, 13, 8, 0, 0),
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        assert provider.has_persisted_workflow(db, str(task.id)) is True
        assert provider.find_persisted_task(db, str(task.id)) is not None
