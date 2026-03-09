import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.engine.conversion_service import ConversionService
from db.database import Base


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
    assert "workflow:" in yaml_output
