from __future__ import annotations

import pytest

from core.engine.conversion_service import ConversionService

from .coze_workflow_corpus import CORPUS_CASES
from .semantic_harness import execute_dify_workflow, execute_ir_workflow
from .semantic_oracles import load_semantic_oracle


SEMANTIC_CASES = [case for case in CORPUS_CASES if case.semantic_oracle is not None]


def test_semantic_corpus_cases_exist() -> None:
    assert [case.name for case in SEMANTIC_CASES] == [
        "baseline_start_end",
        "output_emitter_passthrough",
        "output_emitter_literal_supported_duplicate",
        "chatflow_output_emitter_globals",
        "comment_annotation",
        "code_python_uppercase",
    ]


@pytest.mark.parametrize("case", SEMANTIC_CASES, ids=lambda case: case.name)
def test_supported_cases_match_ir_and_dify_terminal_semantics(case) -> None:
    service = ConversionService()
    ir_workflow = service.engine.coze_parser.parse_dict(case.canvas)

    dsl, report = service.engine.convert_from_ir(ir_workflow)
    expected_terminal = load_semantic_oracle(case.semantic_oracle or case.name)

    assert report.supported is True
    assert report.requires_manual_review is case.expected_manual_review
    assert dsl is not None
    assert execute_ir_workflow(ir_workflow, case.semantic_inputs) == expected_terminal
    assert execute_dify_workflow(dsl, case.semantic_inputs) == expected_terminal
