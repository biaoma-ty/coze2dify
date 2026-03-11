import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.engine.conversion_service import ConversionService
from core.ir.models import IREdge, IRNode, IRPosition, IRVariable, IRWorkflow
from core.ir.types import IRNodeType, IRVariableType
from db.database import Base
from db.models import MigrationTask, SyncConfig


MINIMAL_COZE_CANVAS = {
    "nodes": [
        {
            "id": "start-node",
            "type": "1",
            "meta": {"position": {"x": 0, "y": 0}},
            "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
        },
        {
            "id": "end-node",
            "type": "2",
            "meta": {"position": {"x": 320, "y": 0}},
            "data": {"inputs": {"terminatePlan": "useAnswerContent"}},
        },
    ],
    "edges": [
        {
            "sourceNodeID": "start-node",
            "targetNodeID": "end-node",
        }
    ],
    "versions": {},
}


def test_convert_uploaded_file_persists_artifacts(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    with session_factory() as db:
        result = service.convert_uploaded_file(
            db,
            json.dumps(MINIMAL_COZE_CANVAS).encode(),
            "workflow.json",
        )
        persisted = service.get_conversion(db, result["conversion_id"])
        yaml_output = service.get_yaml(db, result["conversion_id"])

    assert result["status"] == "converted"
    assert result["report"]["total_nodes"] == 2
    assert persisted["source_workflow_name"] == "workflow.json"
    assert persisted["dsl"]["workflow"]["graph"]["nodes"]
    assert persisted["dsl"]["workflow"]["graph"]["edges"]
    assert result["source_graph"]["node_count"] == 2
    assert result["source_graph"]["edge_count"] == 1
    assert result["target_graph"]["node_count"] == 2
    assert result["target_graph"]["edge_count"] == 1
    assert "workflow:" in yaml_output


def test_get_conversion_includes_nested_source_graph_summary(tmp_path, monkeypatch) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-nested-source-graph.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    workflow = IRWorkflow(
        id="nested-source",
        name="Nested source",
        nodes=[
            IRNode(
                id="start",
                node_type=IRNodeType.START,
                title="Start",
                position=IRPosition(),
            ),
            IRNode(
                id="loop",
                node_type=IRNodeType.LOOP_ARRAY,
                title="Loop",
                position=IRPosition(x=280, y=0),
                children=[
                    IRNode(
                        id="child-code",
                        node_type=IRNodeType.CODE,
                        title="Child Code",
                        position=IRPosition(x=560, y=0),
                        outputs=[IRVariable(name="result", var_type=IRVariableType.STRING)],
                    )
                ],
                child_edges=[
                    IREdge(source_node_id="loop", target_node_id="child-code"),
                ],
            ),
            IRNode(
                id="end",
                node_type=IRNodeType.END,
                title="End",
                position=IRPosition(x=840, y=0),
            ),
        ],
        edges=[
            IREdge(source_node_id="start", target_node_id="loop"),
            IREdge(source_node_id="loop", target_node_id="end"),
        ],
    )

    monkeypatch.setattr(service.engine.coze_parser, "parse_file", lambda content, fmt: workflow)

    with session_factory() as db:
        result = service.convert_uploaded_file(db, b"{}", "nested.json")
        persisted = service.get_conversion(db, result["conversion_id"])

    source_nodes = {node["id"]: node for node in persisted["source_graph"]["nodes"]}

    assert persisted["source_graph"]["node_count"] == 4
    assert persisted["source_graph"]["edge_count"] == 3
    assert source_nodes["loop"]["parent_id"] is None
    assert source_nodes["child-code"]["parent_id"] == "loop"
    assert result["status"] == "blocked"
    assert result["report"]["supported"] is False
    assert persisted["target_graph"] is None
    assert persisted["dsl"] == {}


def test_list_conversions_returns_paginated_history_without_sync_tasks(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    with session_factory() as db:
        first = service.convert_uploaded_file(
            db,
            json.dumps(MINIMAL_COZE_CANVAS).encode(),
            "first.json",
        )
        second = service.convert_uploaded_file(
            db,
            json.dumps(MINIMAL_COZE_CANVAS).encode(),
            "second.json",
        )

        latest_task = db.get(MigrationTask, int(second["conversion_id"]))
        assert latest_task is not None
        latest_snapshot = dict(latest_task.ir_snapshot or {})
        latest_snapshot["write_result"] = {
            "app_id": "app-history-123",
            "mode": "create",
            "db_url": "postgresql://dify.example/db",
            "written_at": "2026-03-09T12:34:56+00:00",
        }
        latest_task.ir_snapshot = latest_snapshot
        latest_task.status = "written"
        db.add(latest_task)

        sync_config = SyncConfig(
            name="Nightly sync",
            coze_db_url="postgresql://coze.example/db",
            dify_db_url="postgresql://dify.example/db",
        )
        db.add(sync_config)
        db.flush()
        db.add(
            MigrationTask(
                sync_config_id=sync_config.id,
                source_type="database",
                source_workflow_id="sync-only",
                source_workflow_name="Sync-only workflow",
                status="converted",
                ir_snapshot={"write_result": None},
                report={"total_nodes": 0},
            )
        )
        db.commit()

        first_page = service.list_conversions(db, limit=1, offset=0)
        second_page = service.list_conversions(db, limit=1, offset=1)

    assert first_page["total"] == 2
    assert [item["conversion_id"] for item in first_page["items"]] == [second["conversion_id"]]
    assert first_page["items"][0]["status"] == "written"
    assert first_page["items"][0]["write_result"]["app_id"] == "app-history-123"
    assert first_page["items"][0]["write_result"]["target"]["display_url"] == "postgresql://***@dify.example/db"
    assert first_page["items"][0]["report_summary"]["total_nodes"] == 2
    assert first_page["items"][0]["report_summary"]["mapped_count"] >= 0
    assert [item["conversion_id"] for item in second_page["items"]] == [first["conversion_id"]]


def test_write_to_dify_persists_redacted_write_audit(tmp_path, monkeypatch) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-write-success.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    class SuccessfulWriter:
        def __init__(self, db_url: str) -> None:
            self.db_url = db_url

        def write_workflow(self, dify_dsl) -> str:  # noqa: ANN001 - test double
            return "app-created-123"

    monkeypatch.setattr("core.engine.conversion_service.DifyDbWriter", SuccessfulWriter)

    with session_factory() as db:
        conversion = service.convert_uploaded_file(
            db,
            json.dumps(MINIMAL_COZE_CANVAS).encode(),
            "write-success.json",
        )
        write_result = service.write_to_dify(
            db,
            conversion["conversion_id"],
            db_url="postgresql://writer:supersecret@dify.example:5432/dify",
        )
        persisted = service.get_conversion(db, conversion["conversion_id"])

    assert write_result["status"] == "written"
    assert write_result["write_result"]["target"]["display_url"] == "postgresql://***@dify.example:5432/dify"
    assert write_result["write_result"]["status"] == "succeeded"
    assert persisted["audit"]["last_write"]["app_id"] == "app-created-123"
    assert persisted["error_message"] is None


def test_write_to_dify_persists_sanitized_failure_details(tmp_path, monkeypatch) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-write-failure.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    class FailingWriter:
        def __init__(self, db_url: str) -> None:
            self.db_url = db_url

        def write_workflow(self, dify_dsl) -> str:  # noqa: ANN001 - test double
            raise RuntimeError(f"unable to connect to {self.db_url}")

    monkeypatch.setattr("core.engine.conversion_service.DifyDbWriter", FailingWriter)

    with session_factory() as db:
        conversion = service.convert_uploaded_file(
            db,
            json.dumps(MINIMAL_COZE_CANVAS).encode(),
            "write-failure.json",
        )

        with pytest.raises(RuntimeError, match=r"postgresql://\*\*\*@dify.example:5432/dify"):
            service.write_to_dify(
                db,
                conversion["conversion_id"],
                db_url="postgresql://writer:supersecret@dify.example:5432/dify",
            )

        persisted = service.get_conversion(db, conversion["conversion_id"])

    assert persisted["status"] == "write_failed"
    assert persisted["error_message"] == "unable to connect to postgresql://***@dify.example:5432/dify"
    assert persisted["write_result"]["status"] == "failed"
    assert persisted["write_result"]["target"]["display_url"] == "postgresql://***@dify.example:5432/dify"
