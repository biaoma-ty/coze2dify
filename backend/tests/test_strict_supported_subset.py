from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.engine.conversion_service import ConversionService
from db.database import Base

from .coze_workflow_corpus import CORPUS_CASES
from .semantic_harness import execute_dify_workflow, execute_ir_workflow

_SNAPSHOT_DIR = Path(__file__).with_name("golden").joinpath("strict_supported_subset")


def test_strict_subset_corpus_contains_42_cases() -> None:
    assert len(CORPUS_CASES) == 42


@pytest.mark.parametrize("case", CORPUS_CASES, ids=lambda case: case.name)
def test_strict_subset_blocks_or_allows_cases_as_declared(case) -> None:
    service = ConversionService()
    dsl, report = service.engine.convert_from_dict(case.canvas)

    assert report.supported is case.expected_supported
    assert report.requires_manual_review is case.expected_manual_review
    assert (dsl is not None) is case.expected_supported


@pytest.mark.parametrize(
    "case",
    [case for case in CORPUS_CASES if case.expected_terminal is not None],
    ids=lambda case: case.name,
)
def test_strict_subset_semantic_equivalence_for_supported_cases(case) -> None:
    service = ConversionService()
    ir_workflow = service.engine.coze_parser.parse_dict(case.canvas)
    dsl, report = service.engine.convert_from_ir(ir_workflow)

    assert report.supported is True
    assert dsl is not None
    assert execute_ir_workflow(ir_workflow, case.semantic_inputs) == case.expected_terminal
    assert execute_dify_workflow(dsl, case.semantic_inputs) == case.expected_terminal


@pytest.mark.parametrize(
    "case",
    [case for case in CORPUS_CASES if case.golden_snapshot],
    ids=lambda case: case.name,
)
def test_strict_subset_golden_snapshots(case) -> None:
    service = ConversionService()
    dsl, report = service.engine.convert_from_dict(case.canvas)
    assert report.supported is True
    assert dsl is not None

    expected_snapshot = yaml.safe_load((_SNAPSHOT_DIR / f"{case.golden_snapshot}.yml").read_text())
    actual_snapshot = yaml.safe_load(service.engine.dify_generator.to_yaml(dsl))
    assert actual_snapshot == expected_snapshot


def test_unsupported_workflow_is_persisted_as_blocked(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-strict-subset.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    unsupported_case = next(case for case in CORPUS_CASES if case.name == "llm_chat")

    with session_factory() as db:
        conversion = service.convert_uploaded_file(db, yaml.safe_dump(unsupported_case.canvas).encode(), "blocked.yaml")
        persisted = service.get_conversion(db, conversion["conversion_id"])
        with pytest.raises(LookupError, match="has no DSL artifact"):
            service.get_yaml(db, conversion["conversion_id"])

    assert conversion["status"] == "blocked"
    assert conversion["report"]["supported"] is False
    assert conversion["report"]["blocking_issues"]
    assert persisted["dsl"] == {}
    assert persisted["error_message"] == conversion["report"]["blocking_issues"][0]


def test_write_to_dify_requires_manual_review_confirmation(tmp_path, monkeypatch) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-manual-review.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()
    python_case = next(case for case in CORPUS_CASES if case.name == "code_python_uppercase")

    class SuccessfulWriter:
        def __init__(self, db_url: str) -> None:
            self.db_url = db_url

        def write_workflow(self, dify_dsl) -> str:  # noqa: ANN001 - test double
            return "app-reviewed-123"

    monkeypatch.setattr("core.engine.conversion_service.DifyDbWriter", SuccessfulWriter)

    with session_factory() as db:
        conversion = service.convert_uploaded_file(db, yaml.safe_dump(python_case.canvas).encode(), "python-code.yaml")

        with pytest.raises(ValueError, match="manual review"):
            service.write_to_dify(
                db,
                conversion["conversion_id"],
                db_url="postgresql://writer:supersecret@dify.example:5432/dify",
            )

        write_result = service.write_to_dify(
            db,
            conversion["conversion_id"],
            db_url="postgresql://writer:supersecret@dify.example:5432/dify",
            confirm_reviewed=True,
        )

    assert conversion["report"]["requires_manual_review"] is True
    assert write_result["status"] == "written"
