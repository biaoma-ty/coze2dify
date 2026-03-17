from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_ORACLE_DIR = Path(__file__).with_name("golden").joinpath("semantic_oracles")


@dataclass(frozen=True)
class SemanticOracleCase:
    name: str
    canvas: dict[str, Any]
    inputs: dict[str, Any]
    oracle_name: str


def load_semantic_oracle(name: str) -> dict[str, Any]:
    return yaml.safe_load((_ORACLE_DIR / f"{name}.yml").read_text())


def llm_canvas_with_list_params() -> dict[str, Any]:
    return {
        "mode": "chatflow",
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {
                    "outputs": [
                        {"type": "string", "name": "input", "required": True},
                    ]
                },
            },
            {
                "id": "retriever",
                "type": "5",
                "meta": {"position": {"x": 280, "y": 0}},
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
                "meta": {"position": {"x": 560, "y": 0}},
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
                                "name": "temperature",
                                "input": {"type": "float", "value": {"type": "literal", "content": "0.3"}},
                            },
                            {
                                "name": "maxTokens",
                                "input": {"type": "integer", "value": {"type": "literal", "content": "2048"}},
                            },
                            {
                                "name": "topP",
                                "input": {"type": "float", "value": {"type": "literal", "content": "0.95"}},
                            },
                            {
                                "name": "modleName",
                                "input": {
                                    "type": "string",
                                    "value": {"type": "literal", "content": "DeepSeek-V3-0324"},
                                },
                            },
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


def llm_canvas_with_ordered_messages_and_memory() -> dict[str, Any]:
    return {
        "mode": "chatflow",
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {
                    "outputs": [
                        {"type": "string", "name": "input", "required": True},
                    ]
                },
            },
            {
                "id": "retriever",
                "type": "5",
                "meta": {"position": {"x": 280, "y": 0}},
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
                "meta": {"position": {"x": 560, "y": 0}},
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
                            {
                                "name": "persona",
                                "input": {
                                    "type": "string",
                                    "value": {"type": "literal", "content": "Grounded analyst"},
                                },
                            },
                        ],
                        "llmParam": [
                            {
                                "name": "messages",
                                "input": {
                                    "type": "list",
                                    "value": {
                                        "type": "literal",
                                        "content": [
                                            {"role": "system", "text": "Persona: {{persona}}"},
                                            {"role": "assistant", "text": "Retrieved: {{context}}"},
                                            {"role": "user", "text": "Question: {{input}}"},
                                        ],
                                    },
                                },
                            },
                            {
                                "name": "memoryQueryPromptTemplate",
                                "input": {
                                    "type": "string",
                                    "value": {
                                        "type": "literal",
                                        "content": "Recall the latest user request: {{input}}",
                                    },
                                },
                            },
                            {
                                "name": "memoryRolePrefix",
                                "input": {
                                    "type": "object",
                                    "value": {
                                        "type": "literal",
                                        "content": {"assistant": "Dify", "user": "User"},
                                    },
                                },
                            },
                            {
                                "name": "enableChatHistory",
                                "input": {"type": "boolean", "value": {"type": "literal", "content": True}},
                            },
                            {
                                "name": "chatHistoryRound",
                                "input": {"type": "integer", "value": {"type": "literal", "content": "4"}},
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


LLM_SEMANTIC_ORACLE_CASES = [
    SemanticOracleCase(
        name="llm_prompt_context_memory",
        canvas=llm_canvas_with_list_params(),
        inputs={"input": "What is the answer?"},
        oracle_name="llm_prompt_context_memory",
    ),
    SemanticOracleCase(
        name="llm_prompt_order_memory",
        canvas=llm_canvas_with_ordered_messages_and_memory(),
        inputs={"input": "What is the answer?"},
        oracle_name="llm_prompt_order_memory",
    ),
]
