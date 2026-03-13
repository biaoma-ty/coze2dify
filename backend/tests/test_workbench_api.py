from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.endpoints.workbench import service
from api.router import api_router


def _make_client() -> TestClient:
    service.reset()
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    return TestClient(app)


def test_workbench_overview_and_batch_migrate_flow() -> None:
    client = _make_client()

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


def test_workbench_analysis_endpoints_return_expected_payloads() -> None:
    client = _make_client()

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


def test_workbench_tests_review_release_and_sandbox_mutations() -> None:
    client = _make_client()

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
