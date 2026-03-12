from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.engine.conversion_service import ConversionService
from db.database import Base

from .coze_workflow_corpus import CORPUS_CASES


_SUPPORTED_CANVAS = {
    "nodes": [
        {
            "id": "start",
            "type": "1",
            "meta": {"position": {"x": 0, "y": 0}},
            "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
        },
        {
            "id": "answer",
            "type": "13",
            "meta": {"position": {"x": 320, "y": 0}},
            "data": {
                "inputs": {
                    "inputParameters": [
                        {
                            "name": "answer",
                            "input": {
                                "type": "string",
                                "value": {
                                    "type": "ref",
                                    "content": {
                                        "blockID": "start",
                                        "name": "input",
                                        "path": [],
                                        "source": "block-output",
                                    },
                                },
                            },
                        }
                    ]
                }
            },
        },
    ],
    "edges": [{"sourceNodeID": "start", "targetNodeID": "answer"}],
    "versions": {},
}

_BLOCKED_CANVAS = {
    "nodes": [
        {
            "id": "start",
            "type": "1",
            "meta": {"position": {"x": 0, "y": 0}},
            "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
        },
        {
            "id": "llm",
            "type": "3",
            "meta": {"position": {"x": 320, "y": 0}},
            "data": {"inputs": {}},
        },
    ],
    "edges": [{"sourceNodeID": "start", "targetNodeID": "llm"}],
    "versions": {},
}

_MANUAL_REVIEW_CANVAS = next(case.canvas for case in CORPUS_CASES if case.name == "code_python_uppercase")


def test_strict_subset_allows_supported_workflow() -> None:
    service = ConversionService()

    dsl, report = service.engine.convert_from_dict(_SUPPORTED_CANVAS)

    assert report.supported is True
    assert report.blocking_issues == []
    assert dsl is not None
    assert dsl.workflow.graph.nodes


def test_strict_subset_blocks_partial_or_unmappable_workflow() -> None:
    service = ConversionService()

    dsl, report = service.engine.convert_from_dict(_BLOCKED_CANVAS)

    assert report.supported is False
    assert dsl is None
    assert report.blocking_issues
    assert report.node_results[1].support_state == "blocked"


def test_strict_subset_admits_python_code_only_with_manual_review() -> None:
    service = ConversionService()

    dsl, report = service.engine.convert_from_dict(_MANUAL_REVIEW_CANVAS)

    assert report.supported is True
    assert report.requires_manual_review is True
    assert report.manual_review_reasons
    assert dsl is not None
    assert report.node_results[1].support_state == "manual_review"


def test_blocked_workflow_is_persisted_without_dsl_artifact(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-blocked.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    with session_factory() as db:
        conversion = service.convert_uploaded_file(
            db,
            json.dumps(_BLOCKED_CANVAS).encode(),
            "blocked.json",
        )
        persisted = service.get_conversion(db, conversion["conversion_id"])

        with pytest.raises(LookupError, match="has no DSL artifact"):
            service.get_yaml(db, conversion["conversion_id"])

        with pytest.raises(ValueError, match="strict supported subset"):
            service.write_to_dify(
                db,
                conversion["conversion_id"],
                db_url="postgresql://writer:supersecret@dify.example:5432/dify",
            )

    assert conversion["status"] == "blocked"
    assert conversion["report"]["supported"] is False
    assert persisted["dsl"] == {}
    assert persisted["target_graph"] is None
    assert persisted["error_message"] == conversion["report"]["blocking_issues"][0]
