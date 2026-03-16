from __future__ import annotations

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator

from .semantic_harness import execute_dify_workflow, execute_ir_workflow


def test_semantic_harness_preserves_global_state_variables_in_answer_output() -> None:
    workflow = CozeParser().parse_dict(
        {
            "mode": "chatflow",
            "variables": [
                {
                    "name": "app_name",
                    "type": "string",
                    "source": "global_variable_app",
                    "defaultValue": "Acme",
                },
                {
                    "name": "memory",
                    "type": "string",
                    "source": "global_variable_user",
                    "defaultValue": "Carry forward",
                },
            ],
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
                                    "name": "part1",
                                    "input": {"type": "string", "value": {"type": "literal", "content": "App"}},
                                },
                                {
                                    "name": "part2",
                                    "input": {
                                        "type": "string",
                                        "value": {
                                            "type": "ref",
                                            "content": {
                                                "blockID": "",
                                                "name": "app_name",
                                                "path": [],
                                                "source": "global_variable_app",
                                            },
                                        },
                                    },
                                },
                                {
                                    "name": "part3",
                                    "input": {"type": "string", "value": {"type": "literal", "content": "Memory"}},
                                },
                                {
                                    "name": "part4",
                                    "input": {
                                        "type": "string",
                                        "value": {
                                            "type": "ref",
                                            "content": {
                                                "blockID": "",
                                                "name": "memory",
                                                "path": [],
                                                "source": "global_variable_user",
                                            },
                                        },
                                    },
                                },
                            ]
                        }
                    },
                },
            ],
            "edges": [{"sourceNodeID": "start", "targetNodeID": "answer"}],
            "versions": {},
        }
    )
    dsl = DifyGenerator().generate(workflow)

    expected_terminal = {"answer": "App\nAcme\nMemory\nCarry forward"}

    assert execute_ir_workflow(workflow, {"input": "ignored"}) == expected_terminal
    assert execute_dify_workflow(dsl, {"input": "ignored"}) == expected_terminal


def test_semantic_harness_compares_llm_prompt_context_and_memory_traces() -> None:
    workflow = CozeParser().parse_dict(
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
                    "id": "retriever",
                    "type": "5",
                    "meta": {"position": {"x": 320, "y": 0}},
                    "data": {
                        "inputs": {
                            "code": "def main(): return {'context': 'facts'}",
                            "language": 1,
                            "outputParameters": [{"name": "context", "input": {"type": "string"}}],
                        }
                    },
                },
                {
                    "id": "llm",
                    "type": "3",
                    "meta": {"position": {"x": 640, "y": 0}},
                    "data": {
                        "inputs": {
                            "inputParameters": [
                                {
                                    "name": "input",
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
                                },
                                {
                                    "name": "context",
                                    "input": {
                                        "type": "string",
                                        "value": {
                                            "type": "ref",
                                            "content": {
                                                "blockID": "retriever",
                                                "name": "context",
                                                "path": [],
                                                "source": "block-output",
                                            },
                                        },
                                    },
                                },
                            ],
                            "llmParam": [
                                {
                                    "name": "prompt",
                                    "input": {
                                        "type": "string",
                                        "value": {
                                            "type": "literal",
                                            "content": "Question: {{input}}\nContext: {{context}}",
                                        },
                                    },
                                },
                                {
                                    "name": "systemPrompt",
                                    "input": {
                                        "type": "string",
                                        "value": {"type": "literal", "content": "You are a grounded assistant."},
                                    },
                                },
                                {
                                    "name": "enableChatHistory",
                                    "input": {"type": "boolean", "value": {"type": "literal", "content": True}},
                                },
                                {
                                    "name": "chatHistoryRound",
                                    "input": {"type": "integer", "value": {"type": "literal", "content": "6"}},
                                },
                            ],
                        }
                    },
                },
            ],
            "edges": [
                {"sourceNodeID": "start", "targetNodeID": "retriever"},
                {"sourceNodeID": "retriever", "targetNodeID": "llm"},
            ],
            "versions": {},
        }
    )
    dsl = DifyGenerator().generate(workflow)

    expected_trace = {
        "prompt": [
            {"role": "system", "text": "You are a grounded assistant."},
            {"role": "user", "text": "Question: What is the answer?\nContext: facts"},
        ],
        "context": "facts",
        "memory": {"enabled": True, "size": 6},
    }

    assert execute_ir_workflow(workflow, {"input": "What is the answer?"}) == expected_trace
    assert execute_dify_workflow(dsl, {"input": "What is the answer?"}) == expected_trace
