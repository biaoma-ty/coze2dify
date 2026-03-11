from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.sync.sync_engine import SyncEngine
from core.sync.conflict_resolver import ConflictStrategy
from core.engine.conversion_service import ConversionService
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

    def read_workflow(self, workflow_id: str) -> dict[str, object] | None:
        return {
            "id": workflow_id,
            "name": f"Workflow {workflow_id}",
            "canvas": _minimal_canvas(workflow_id),
        }


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


class PreviewCozeReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_workflows(self) -> list[dict[str, str]]:
        return [
            {"id": "wf-create", "name": "Create Flow"},
            {"id": "wf-update", "name": "Update Flow"},
            {"id": "wf-skip", "name": "Skip Flow"},
            {"id": "wf-conflict", "name": "Name Collision"},
        ]

    def read_workflow(self, workflow_id: str) -> dict[str, object] | None:
        canvas = _minimal_canvas(workflow_id)
        return {
            "id": workflow_id,
            "name": {
                "wf-create": "Create Flow",
                "wf-update": "Update Flow",
                "wf-skip": "Skip Flow",
                "wf-conflict": "Name Collision",
            }[workflow_id],
            "canvas": canvas,
        }


class PreviewDifyReader:
    def __init__(self, db_url: str, workflows: dict[str, dict[str, object]]) -> None:
        self.db_url = db_url
        self.workflows = workflows

    def list_apps(self) -> list[dict[str, str]]:
        return [
            {"app_id": "app-update", "name": "Update Flow"},
            {"app_id": "app-skip", "name": "Skip Flow"},
            {"app_id": "app-name-collision", "name": "Name Collision"},
        ]

    def read_workflow(self, app_id: str) -> dict[str, object] | None:
        return self.workflows.get(app_id)


class EmptyCozeReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_workflows(self) -> list[dict[str, str]]:
        return []

    def read_workflow(self, workflow_id: str) -> dict[str, object] | None:
        return None


class DeletePreviewDifyReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_apps(self) -> list[dict[str, str]]:
        return [
            {"app_id": "app-delete", "name": "Deleted Flow"},
        ]

    def read_workflow(self, app_id: str) -> dict[str, object] | None:
        if app_id != "app-delete":
            return None
        return {"app_id": app_id, "graph": {"nodes": [], "edges": []}, "features": {}}


class EmptyDifyReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_apps(self) -> list[dict[str, str]]:
        return []

    def read_workflow(self, app_id: str) -> dict[str, object] | None:
        return None


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
            report={"workflow_name": workflow_id, "total_nodes": 1, "supported": True, "blocking_issues": []},
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


class BlockedConversionService(FakeConversionService):
    def convert_from_db(self, db, *, db_url: str, workflow_id: str) -> dict[str, object]:
        blocking_issue = "LLM is blocked by the strict supported subset because its mapping is partial."
        task = MigrationTask(
            source_type="database",
            source_workflow_id=workflow_id,
            source_workflow_name=f"Workflow {workflow_id}",
            status="blocked",
            ir_snapshot={"dify_dsl": None, "write_result": None},
            dify_dsl=None,
            report={
                "workflow_name": workflow_id,
                "total_nodes": 2,
                "supported": False,
                "blocking_issues": [blocking_issue],
            },
            error_message=blocking_issue,
            completed_at=_utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {
            "conversion_id": str(task.id),
            "dsl": {},
            "report": task.report,
            "status": task.status,
        }


def _minimal_canvas(node_id: str) -> dict[str, object]:
    start_id = f"{node_id}-start"
    end_id = f"{node_id}-end"
    return {
        "nodes": [
            {
                "id": start_id,
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
            },
            {
                "id": end_id,
                "type": "2",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {"inputs": {"terminatePlan": "useAnswerContent"}},
            },
        ],
        "edges": [{"sourceNodeID": start_id, "targetNodeID": end_id}],
        "versions": {},
    }


def _blocked_canvas(node_id: str) -> dict[str, object]:
    start_id = f"{node_id}-start"
    llm_id = f"{node_id}-llm"
    return {
        "nodes": [
            {
                "id": start_id,
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
            },
            {
                "id": llm_id,
                "type": "3",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {"inputs": {}},
            },
        ],
        "edges": [{"sourceNodeID": start_id, "targetNodeID": llm_id}],
        "versions": {},
    }


def _dsl_payload_for(canvas: dict[str, object]) -> dict[str, object]:
    service = ConversionService()
    ir_workflow = service.engine.coze_parser.parse_dict(canvas)
    dsl, _report = service.engine.convert_from_ir(ir_workflow)
    return dsl.model_dump(mode="json")


class BlockedPreviewCozeReader:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url

    def list_workflows(self) -> list[dict[str, str]]:
        return [{"id": "wf-blocked", "name": "Blocked Flow"}]

    def read_workflow(self, workflow_id: str) -> dict[str, object] | None:
        return {
            "id": workflow_id,
            "name": "Blocked Flow",
            "canvas": _blocked_canvas(workflow_id),
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
        synced_tasks = (
            db.execute(select(MigrationTask).where(MigrationTask.sync_config_id == config.id)).scalars().all()
        )

    assert result["status"] == "completed"
    assert result["summary"] == {
        "created": 1,
        "updated": 1,
        "failed": 0,
        "skipped": 0,
        "unsupported": 0,
        "conflicts": 0,
    }
    assert result["delete_policy"]["mode"] == "observe_only"
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


def test_preview_diff_detects_create_update_skip_and_conflict_without_persisting_tasks(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-preview.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    skip_payload = _dsl_payload_for(_minimal_canvas("wf-skip"))
    update_payload = _dsl_payload_for(_minimal_canvas("wf-update"))
    update_workflow = {
        "app_id": "app-update",
        "graph": {"nodes": [{"id": "changed-node"}], "edges": []},
        "features": update_payload["workflow"]["features"],
    }
    skip_workflow = {
        "app_id": "app-skip",
        "graph": skip_payload["workflow"]["graph"],
        "features": skip_payload["workflow"]["features"],
    }

    sync_engine = SyncEngine(
        ConversionService(),
        coze_reader_factory=PreviewCozeReader,
        dify_reader_factory=lambda db_url: PreviewDifyReader(
            db_url,
            {"app-update": update_workflow, "app-skip": skip_workflow},
        ),
    )

    with session_factory() as db:
        config = SyncConfig(
            name="Diff Preview",
            coze_db_url="postgresql://coze.test/app",
            dify_db_url="postgresql://dify.test/app",
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        db.add_all(
            [
                MigrationTask(
                    sync_config_id=config.id,
                    source_type="database",
                    source_workflow_id="wf-update",
                    source_workflow_name="Update Flow",
                    status="written",
                    ir_snapshot={"write_result": {"app_id": "app-update", "mode": "create"}},
                    dify_dsl="workflow: {}\n",
                    report={},
                    completed_at=_utcnow(),
                ),
                MigrationTask(
                    sync_config_id=config.id,
                    source_type="database",
                    source_workflow_id="wf-skip",
                    source_workflow_name="Skip Flow",
                    status="written",
                    ir_snapshot={"write_result": {"app_id": "app-skip", "mode": "create"}},
                    dify_dsl="workflow: {}\n",
                    report={},
                    completed_at=_utcnow(),
                ),
            ]
        )
        db.commit()

        result = sync_engine.preview_diff(db, config)
        task_count = db.execute(select(MigrationTask)).scalars().all()

    assert result["status"] == "partial"
    assert result["summary"] == {
        "created": 1,
        "updated": 1,
        "failed": 0,
        "skipped": 1,
        "unsupported": 0,
        "conflicts": 1,
    }
    assert {item["source_workflow_id"] for item in result["items"]} == {
        "wf-create",
        "wf-update",
        "wf-skip",
        "wf-conflict",
    }
    assert len(task_count) == 2


def test_preview_diff_records_delete_intent_under_selected_policy(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-delete-preview.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    sync_engine = SyncEngine(
        ConversionService(),
        coze_reader_factory=EmptyCozeReader,
        dify_reader_factory=DeletePreviewDifyReader,
    )

    with session_factory() as db:
        config = SyncConfig(
            name="Delete Preview",
            coze_db_url="postgresql://coze.test/app",
            dify_db_url="postgresql://dify.test/app",
            delete_mode="approval_required",
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        db.add(
            MigrationTask(
                sync_config_id=config.id,
                source_type="database",
                source_workflow_id="wf-delete",
                source_workflow_name="Deleted Flow",
                status="written",
                ir_snapshot={"write_result": {"app_id": "app-delete", "mode": "create"}},
                dify_dsl="workflow: {}\n",
                report={},
                completed_at=_utcnow(),
            )
        )
        db.commit()

        result = sync_engine.preview_diff(db, config)

    assert result["status"] == "partial"
    assert result["summary"]["unsupported"] == 1
    assert result["delete_policy"]["mode"] == "approval_required"
    assert result["items"][0]["action"] == "delete"
    assert result["items"][0]["status"] == "unsupported"
    assert result["items"][0]["delete_policy"]["mode"] == "approval_required"
    assert result["items"][0]["delete_policy"]["intent_status"] == "approval_pending"


def test_preview_diff_marks_blocked_conversions_as_unsupported(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-blocked-preview.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    sync_engine = SyncEngine(
        ConversionService(),
        coze_reader_factory=BlockedPreviewCozeReader,
        dify_reader_factory=EmptyDifyReader,
    )

    with session_factory() as db:
        config = SyncConfig(
            name="Blocked Preview",
            coze_db_url="postgresql://coze.test/app",
            dify_db_url="postgresql://dify.test/app",
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        result = sync_engine.preview_diff(db, config)
        persisted_tasks = db.execute(select(MigrationTask)).scalars().all()

    assert result["status"] == "partial"
    assert result["summary"] == {
        "created": 0,
        "updated": 0,
        "failed": 0,
        "skipped": 0,
        "unsupported": 1,
        "conflicts": 0,
    }
    assert len(result["items"]) == 1
    assert result["items"][0]["status"] == "unsupported"
    assert "strict supported subset" in result["items"][0]["message"]
    assert persisted_tasks == []


def test_execute_sync_skips_write_for_blocked_conversions(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-blocked-execute.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    conversion_service = BlockedConversionService()
    sync_engine = SyncEngine(
        conversion_service,
        coze_reader_factory=BlockedPreviewCozeReader,
        dify_reader_factory=EmptyDifyReader,
    )

    with session_factory() as db:
        config = SyncConfig(
            name="Blocked Execute",
            coze_db_url="postgresql://coze.test/app",
            dify_db_url="postgresql://dify.test/app",
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        result = sync_engine.execute_sync(db, config)
        synced_tasks = (
            db.execute(select(MigrationTask).where(MigrationTask.sync_config_id == config.id)).scalars().all()
        )

    assert result["status"] == "partial"
    assert result["summary"] == {
        "created": 0,
        "updated": 0,
        "failed": 0,
        "skipped": 0,
        "unsupported": 1,
        "conflicts": 0,
    }
    assert len(result["items"]) == 1
    assert result["items"][0]["status"] == "unsupported"
    assert result["items"][0]["conversion_id"] == "1"
    assert conversion_service.write_calls == []
    assert len(synced_tasks) == 1
    assert synced_tasks[0].status == "blocked"


def test_resolve_conflict_source_wins_updates_history_and_persists_resolution(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-sync-conflict.db'}",
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
            name="Conflict Sync",
            coze_db_url="postgresql://coze.test/app",
            dify_db_url="postgresql://dify.test/app",
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        history = SyncHistory(
            sync_config_id=config.id,
            trigger_type="manual",
            workflows_synced=0,
            workflows_failed=0,
            conflicts_count=1,
            status="partial",
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
                        "source_workflow_id": "wf-update",
                        "source_workflow_name": "Update Flow",
                        "target_app_id": "app-existing",
                        "conversion_id": None,
                        "message": "Manual resolution required.",
                    }
                ],
            },
            started_at=_utcnow(),
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        result = sync_engine.resolve_conflict(
            db,
            history,
            conflict_id="wf-update",
            strategy=ConflictStrategy.SOURCE_WINS,
        )

        refreshed_history = db.get(SyncHistory, history.id)

    assert result["status"] == "completed"
    assert result["summary"] == {
        "created": 0,
        "updated": 1,
        "failed": 0,
        "skipped": 0,
        "unsupported": 0,
        "conflicts": 0,
    }
    assert result["items"][0]["status"] == "updated"
    assert result["items"][0]["resolution"]["strategy"] == "source_wins"
    assert refreshed_history is not None
    assert refreshed_history.workflows_synced == 1
    assert refreshed_history.conflicts_count == 0
    assert conversion_service.write_calls == [("1", "postgresql://dify.test/app", "app-existing")]
