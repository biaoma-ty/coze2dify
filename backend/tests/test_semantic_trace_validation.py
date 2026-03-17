from __future__ import annotations

import pytest

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator
from core.engine.converter import ConversionEngine

from .semantic_harness import execute_dify_workflow, execute_ir_workflow
from .semantic_oracles import LLM_SEMANTIC_ORACLE_CASES, load_semantic_oracle


def test_llm_semantic_oracle_cases_exist() -> None:
    assert [case.name for case in LLM_SEMANTIC_ORACLE_CASES] == [
        "llm_prompt_context_memory",
        "llm_prompt_order_memory",
    ]


@pytest.mark.parametrize("case", LLM_SEMANTIC_ORACLE_CASES, ids=lambda case: case.name)
def test_semantic_harness_matches_explicit_llm_oracles(case) -> None:
    workflow = CozeParser().parse_dict(case.canvas)
    dsl = DifyGenerator().generate(workflow)
    expected_trace = load_semantic_oracle(case.oracle_name)

    assert execute_ir_workflow(workflow, case.inputs) == expected_trace
    assert execute_dify_workflow(dsl, case.inputs) == expected_trace


def test_llm_semantic_validation_reports_unsupported_memory_settings() -> None:
    _, report = ConversionEngine().convert_from_dict(
        {
            "mode": "chatflow",
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
                    "data": {
                        "inputs": {
                            "llmParam": [
                                {
                                    "name": "historyPromptTemplate",
                                    "input": {
                                        "type": "string",
                                        "value": {"type": "literal", "content": "Use full chat history"},
                                    },
                                }
                            ]
                        }
                    },
                },
            ],
            "edges": [{"sourceNodeID": "start", "targetNodeID": "llm"}],
            "versions": {},
        }
    )

    assert any(
        "unsupported Coze prompt/context/memory settings: historyPromptTemplate" in issue
        for issue in report.blocking_issues
    )
