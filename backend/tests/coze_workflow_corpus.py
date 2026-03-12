from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CorpusCase:
    name: str
    canvas: dict[str, Any]
    expected_supported: bool
    expected_manual_review: bool = False
    semantic_inputs: dict[str, Any] = field(default_factory=dict)
    expected_terminal: dict[str, Any] | None = None
    golden_snapshot: str | None = None


def _start_node(*, name: str = "input", var_type: str = "string") -> dict[str, Any]:
    return {
        "id": "start",
        "type": "1",
        "meta": {"position": {"x": 0, "y": 0}},
        "data": {
            "outputs": [
                {
                    "type": var_type,
                    "name": name,
                    "required": True,
                }
            ]
        },
    }


def _end_node() -> dict[str, Any]:
    return {
        "id": "end",
        "type": "2",
        "meta": {"position": {"x": 640, "y": 0}},
        "data": {"inputs": {"terminatePlan": "useAnswerContent"}},
    }


def _reference(block_id: str, name: str, *, source: str = "block-output") -> dict[str, Any]:
    return {
        "type": "ref",
        "content": {
            "blockID": block_id,
            "name": name,
            "path": [],
            "source": source,
        },
    }


def _edge(source: str, target: str) -> dict[str, Any]:
    return {"sourceNodeID": source, "targetNodeID": target}


def _linear_canvas(target_node: dict[str, Any], *, include_end: bool = True) -> dict[str, Any]:
    nodes = [_start_node(), target_node]
    edges = [_edge("start", target_node["id"])]
    if include_end:
        nodes.append(_end_node())
        edges.append(_edge(target_node["id"], "end"))
    return {"nodes": nodes, "edges": edges, "versions": {}}


def _empty_node(case_id: str, type_id: str) -> dict[str, Any]:
    return {
        "id": case_id,
        "type": type_id,
        "meta": {"position": {"x": 320, "y": 0}},
        "data": {"inputs": {}},
    }


def _output_emitter_case(name: str, *, literal: str | None = None) -> CorpusCase:
    if literal is None:
        input_parameters = [
            {
                "name": "answer",
                "input": {
                    "type": "string",
                    "value": _reference("start", "input"),
                },
            }
        ]
    else:
        input_parameters = [
            {
                "name": "answer",
                "input": {
                    "type": "string",
                    "value": {"type": "literal", "content": literal},
                },
            }
        ]

    return CorpusCase(
        name=name,
        canvas={
            "nodes": [
                _start_node(),
                {
                    "id": "answer",
                    "type": "13",
                    "meta": {"position": {"x": 320, "y": 0}},
                    "data": {"inputs": {"inputParameters": input_parameters}},
                },
            ],
            "edges": [_edge("start", "answer")],
            "versions": {},
        },
        expected_supported=True,
        semantic_inputs={"input": "hello world"},
        expected_terminal={"answer": literal or "hello world"},
        golden_snapshot=name,
    )


def _python_code_case() -> CorpusCase:
    return CorpusCase(
        name="code_python_uppercase",
        canvas={
            "nodes": [
                _start_node(),
                {
                    "id": "code",
                    "type": "5",
                    "meta": {"position": {"x": 320, "y": 0}},
                    "data": {
                        "inputs": {
                            "language": 1,
                            "code": ("def main(value):\n    return {'result': value.upper()}\n"),
                            "inputParameters": [
                                {
                                    "name": "value",
                                    "input": {
                                        "type": "string",
                                        "value": _reference("start", "input"),
                                    },
                                }
                            ],
                            "outputParameters": [
                                {
                                    "name": "result",
                                    "input": {"type": "string"},
                                }
                            ],
                        }
                    },
                },
                {
                    "id": "answer",
                    "type": "13",
                    "meta": {"position": {"x": 640, "y": 0}},
                    "data": {
                        "inputs": {
                            "inputParameters": [
                                {
                                    "name": "answer",
                                    "input": {
                                        "type": "string",
                                        "value": _reference("code", "result"),
                                    },
                                }
                            ]
                        }
                    },
                },
            ],
            "edges": [_edge("start", "code"), _edge("code", "answer")],
            "versions": {},
        },
        expected_supported=True,
        expected_manual_review=True,
        semantic_inputs={"input": "hello world"},
        expected_terminal={"answer": "HELLO WORLD"},
        golden_snapshot="code_python_uppercase",
    )


def _baseline_case() -> CorpusCase:
    return CorpusCase(
        name="baseline_start_end",
        canvas={
            "nodes": [_start_node(), _end_node()],
            "edges": [_edge("start", "end")],
            "versions": {},
        },
        expected_supported=True,
        semantic_inputs={"input": "hello world"},
        expected_terminal={},
        golden_snapshot="baseline_start_end",
    )


def _comment_case() -> CorpusCase:
    return CorpusCase(
        name="comment_annotation",
        canvas={
            "nodes": [
                _start_node(),
                _end_node(),
                {
                    "id": "comment",
                    "type": "31",
                    "meta": {"position": {"x": 320, "y": 120}},
                    "data": {"inputs": {}},
                },
            ],
            "edges": [_edge("start", "end")],
            "versions": {},
        },
        expected_supported=True,
        semantic_inputs={"input": "hello world"},
        expected_terminal={},
    )


_BLOCKED_CASE_DEFS: list[tuple[str, str]] = [
    ("code_javascript_blocked", "5"),
    ("llm_chat", "3"),
    ("plugin_tool", "4"),
    ("knowledge_retrieval", "6"),
    ("selector_if_else", "8"),
    ("sub_workflow", "9"),
    ("text_processor", "15"),
    ("question_answer", "18"),
    ("variable_assigner_in_loop", "20"),
    ("loop_count", "21"),
    ("intent_detector", "22"),
    ("knowledge_write", "27"),
    ("batch_parallel", "28"),
    ("continue_node", "29"),
    ("variable_aggregator", "32"),
    ("http_request", "45"),
    ("json_serialize", "58"),
    ("json_deserialize", "59"),
    ("clear_conversation_history", "38"),
    ("create_conversation", "39"),
    ("conversation_update", "51"),
    ("conversation_delete", "52"),
    ("conversation_list", "53"),
    ("conversation_history", "54"),
    ("message_list", "37"),
    ("create_message", "55"),
    ("edit_message", "56"),
    ("delete_message", "57"),
    ("database_custom_sql", "12"),
    ("database_update", "42"),
    ("database_query", "43"),
    ("database_delete", "44"),
    ("database_insert", "46"),
    ("input_receiver", "30"),
    ("break_node", "19"),
    ("variable_assigner", "40"),
    ("knowledge_delete", "60"),
]


def _blocked_case(name: str, type_id: str) -> CorpusCase:
    if name == "code_javascript_blocked":
        node = {
            "id": "target",
            "type": "5",
            "meta": {"position": {"x": 320, "y": 0}},
            "data": {
                "inputs": {
                    "language": 2,
                    "code": "function main(value) { return { result: value.toUpperCase() }; }",
                    "inputParameters": [
                        {
                            "name": "value",
                            "input": {"type": "string", "value": _reference("start", "input")},
                        }
                    ],
                    "outputParameters": [{"name": "result", "input": {"type": "string"}}],
                }
            },
        }
    else:
        node = _empty_node("target", type_id)
    return CorpusCase(
        name=name,
        canvas=_linear_canvas(node),
        expected_supported=False,
    )


CORPUS_CASES: list[CorpusCase] = [
    _baseline_case(),
    _output_emitter_case("output_emitter_passthrough"),
    _output_emitter_case("output_emitter_literal_supported_duplicate", literal="fixed literal"),
    _comment_case(),
    _python_code_case(),
    *[_blocked_case(name, type_id) for name, type_id in _BLOCKED_CASE_DEFS],
]

assert len(CORPUS_CASES) == 42
