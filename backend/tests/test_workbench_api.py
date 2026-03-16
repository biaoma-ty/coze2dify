from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.endpoints.workbench import service
from api.router import api_router
from db.database import Base, get_db
from db.models import MigrationTask, SyncConfig


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _make_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-workbench.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _make_client(session_factory) -> TestClient:
    def override_get_db():
        with session_factory() as db:
            yield db

    service.reset()
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _seed_overview_history(db: Session) -> None:
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


def test_workbench_overview_aggregates_real_conversion_history(tmp_path) -> None:
    session_factory = _make_session_factory(tmp_path)
    with session_factory() as db:
        _seed_overview_history(db)

    client = _make_client(session_factory)
    response = client.get("/api/v1/workbench/overview?limit=10")
    assert response.status_code == 200
    payload = response.json()

    assert payload["summary"] == {
        "totalWorkflows": 3,
        "verifiedWorkflows": 1,
        "averageScore": 83.1,
        "totalNodes": 24,
        "migratedNodes": 16,
        "failedNodes": 8,
        "pendingReviews": 1,
    }

    workflows = payload["workflows"]
    assert [workflow["cozeId"] for workflow in workflows] == ["wf-alpha", "wf-beta", "wf-gamma"]
    assert [workflow["id"] for workflow in workflows] == ["wf-alpha", "wf-beta", "wf-gamma"]

    alpha = workflows[0]
    assert alpha["difyId"] == "app-alpha"
    assert alpha["status"] == "verified"
    assert alpha["score"] == 85.0
    assert alpha["complexity"] == "medium"

    beta = workflows[1]
    assert beta["status"] == "testing"
    assert beta["migrated"] == 7
    assert beta["failed"] == 1
    assert beta["requiresManualReview"] is True

    gamma = workflows[2]
    assert gamma["status"] == "failed"
    assert gamma["score"] == 0.0
    assert gamma["complexity"] == "low"


def test_workbench_mock_overview_and_batch_migrate_flow(tmp_path) -> None:
    client = _make_client(_make_session_factory(tmp_path))

    overview = client.get("/api/v1/workbench/overview?limit=10")
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["summary"] == {
        "totalWorkflows": 5,
        "verifiedWorkflows": 1,
        "averageScore": 89.0,
        "totalNodes": 59,
        "migratedNodes": 47,
        "failedNodes": 6,
        "pendingReviews": 2,
    }
    assert payload["workflows"][2]["status"] == "pending"

    migrated = client.post("/api/v1/workbench/batch-migrate")
    assert migrated.status_code == 200
    migrated_payload = migrated.json()
    assert migrated_payload["workflows"][2]["status"] == "testing"
    assert migrated_payload["workflows"][2]["difyId"] == "app-auto-ghi789"
    assert migrated_payload["workflows"][2]["score"] == 96.4


def test_workbench_batch_migrate_preserves_persisted_overview(tmp_path) -> None:
    session_factory = _make_session_factory(tmp_path)
    with session_factory() as db:
        _seed_overview_history(db)
        db.add(
            MigrationTask(
                source_type="upload",
                source_workflow_id="wf-pending",
                source_workflow_name="Pending Flow",
                status="pending",
                ir_snapshot={},
                report={
                    "workflow_name": "Pending Flow",
                    "supported": True,
                    "requires_manual_review": False,
                    "total_nodes": 5,
                    "mapped_count": 0,
                    "partial_count": 0,
                    "skipped_count": 0,
                },
                completed_at=datetime(2026, 3, 13, 8, 0, 0),
            )
        )
        db.commit()

    client = _make_client(session_factory)

    migrated = client.post("/api/v1/workbench/batch-migrate")
    assert migrated.status_code == 200
    migrated_payload = migrated.json()
    assert all(workflow["id"] != "wf1" for workflow in migrated_payload["workflows"])

    pending = next(workflow for workflow in migrated_payload["workflows"] if workflow["id"] == "wf-pending")
    assert pending["status"] == "testing"
    assert pending["difyId"] == "app-auto-wf-pending"
    assert pending["migrated"] == 5
    assert pending["failed"] == 0
    assert pending["score"] == 96.4

    refreshed = client.get("/api/v1/workbench/overview?limit=10")
    assert refreshed.status_code == 200
    refreshed_pending = next(workflow for workflow in refreshed.json()["workflows"] if workflow["id"] == "wf-pending")
    assert refreshed_pending["status"] == "testing"


def test_workbench_analysis_endpoints_return_expected_payloads(tmp_path) -> None:
    client = _make_client(_make_session_factory(tmp_path))

    topology = client.get("/api/v1/workbench/workflows/wf1/topology")
    assert topology.status_code == 200
    topology_payload = topology.json()
    assert topology_payload["coze"]["nodes"][0]["label"] == "用户输入"
    assert topology_payload["dify"]["nodes"][-1]["label"] == "结束"
    assert len(topology_payload["diffs"]) == 3

    equivalence = client.get("/api/v1/workbench/workflows/wf1/equivalence")
    assert equivalence.status_code == 200
    equivalence_payload = equivalence.json()
    assert equivalence_payload["promptSimilarity"] == 0.88
    assert equivalence_payload["nodes"][3]["status"] == "error"
    assert equivalence_payload["variables"][0]["dify"] == "{{#sys.query#}}"


def test_workbench_tests_review_release_and_sandbox_mutations(tmp_path) -> None:
    client = _make_client(_make_session_factory(tmp_path))

    tests_before = client.get("/api/v1/workbench/workflows/wf1/tests")
    assert tests_before.status_code == 200
    assert len(tests_before.json()["cases"]) == 6

    generated = client.post("/api/v1/workbench/workflows/wf1/tests/generate")
    assert generated.status_code == 200
    generated_payload = generated.json()
    assert generated_payload["generated"] == 1
    assert len(generated_payload["cases"]) == 7

    rerun = client.post("/api/v1/workbench/workflows/wf1/tests/run")
    assert rerun.status_code == 200
    assert rerun.json()["executed"] == 7

    knowledge = client.get("/api/v1/workbench/workflows/wf1/knowledge")
    assert knowledge.status_code == 200
    assert knowledge.json()["records"][2]["ok"] is False

    review = client.get("/api/v1/workbench/workflows/wf1/review")
    assert review.status_code == 200
    assert review.json()["items"][0]["verdict"] is None

    updated_review = client.post(
        "/api/v1/workbench/workflows/wf1/review/r1",
        json={"verdict": "equivalent"},
    )
    assert updated_review.status_code == 200
    updated_review_payload = updated_review.json()
    assert updated_review_payload["item"]["verdict"] == "equivalent"
    assert updated_review_payload["summary"]["pendingReviews"] == 1

    release = client.get("/api/v1/workbench/workflows/wf1/release")
    assert release.status_code == 200
    assert release.json()["traffic"] == 20

    updated_release = client.post(
        "/api/v1/workbench/workflows/wf1/release/traffic",
        json={"traffic": 50},
    )
    assert updated_release.status_code == 200
    assert updated_release.json()["traffic"] == 50
    assert updated_release.json()["stages"][3]["st"] == "active"

    rolled_back = client.post(
        "/api/v1/workbench/workflows/wf1/release/rollback",
        json={"version": "v1.2"},
    )
    assert rolled_back.status_code == 200
    assert next(item for item in rolled_back.json()["versions"] if item["ver"] == "v1.2")["st"] == "active"

    start = client.post("/api/v1/workbench/workflows/wf1/sandbox/start")
    assert start.status_code == 200
    assert start.json()["status"] == "running"

    send = client.post(
        "/api/v1/workbench/workflows/wf1/sandbox/messages",
        json={"text": "查一下最新订单"},
    )
    assert send.status_code == 200
    send_payload = send.json()
    assert send_payload["status"] == "running"
    assert [message["role"] for message in send_payload["messages"]] == ["user", "coze", "dify"]
    assert send_payload["metrics"][0]["coze"] == "143"

    stop = client.post("/api/v1/workbench/workflows/wf1/sandbox/stop")
    assert stop.status_code == 200
    assert stop.json()["status"] == "idle"
    assert stop.json()["messages"] == []

    unknown = client.post("/api/v1/workbench/workflows/not-real/sandbox/start")
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Unknown workflow: not-real"


def test_workbench_persisted_actions_use_real_summary_and_reject_demo_ids(tmp_path) -> None:
    session_factory = _make_session_factory(tmp_path)
    with session_factory() as db:
        _seed_overview_history(db)

    client = _make_client(session_factory)

    updated_review = client.post(
        "/api/v1/workbench/workflows/wf-alpha/review/r1",
        json={"verdict": "equivalent"},
    )
    assert updated_review.status_code == 200
    updated_payload = updated_review.json()
    assert updated_payload["summary"] == {
        "totalWorkflows": 3,
        "verifiedWorkflows": 1,
        "averageScore": 83.1,
        "totalNodes": 24,
        "migratedNodes": 16,
        "failedNodes": 8,
        "pendingReviews": 1,
    }

    demo_workflow = client.get("/api/v1/workbench/workflows/wf1/topology")
    assert demo_workflow.status_code == 404
    assert demo_workflow.json()["detail"] == "Unknown workflow: wf1"

    unknown = client.post("/api/v1/workbench/workflows/not-real/sandbox/start")
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Unknown workflow: not-real"
