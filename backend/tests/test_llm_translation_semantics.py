from __future__ import annotations

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator


def _llm_canvas_with_list_params() -> dict:
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


def test_llm_parser_accepts_real_coze_list_style_parameters() -> None:
    workflow = CozeParser().parse_dict(_llm_canvas_with_list_params())
    llm_node = workflow.nodes[2]

    assert llm_node.config["model"] == "DeepSeek-V3-0324"
    assert llm_node.config["temperature"] == 0.3
    assert llm_node.config["max_tokens"] == 2048
    assert llm_node.config["top_p"] == 0.95
    assert llm_node.config["prompt_template"] == "Question: {{input}}\nContext: {{context}}"
    assert llm_node.config["system_prompt"] == "You are a grounded assistant."
    assert llm_node.config["enable_chat_history"] is True
    assert llm_node.config["chat_history_round"] == 6


def test_llm_generator_emits_context_and_memory_configuration() -> None:
    workflow = CozeParser().parse_dict(_llm_canvas_with_list_params())
    dsl = DifyGenerator().generate(workflow)
    llm_node = next(node for node in dsl.workflow.graph.nodes if node.id == "llm")

    assert llm_node.data.model["name"] == "DeepSeek-V3-0324"
    assert llm_node.data.prompt_template == [
        {"role": "system", "text": "You are a grounded assistant."},
        {"role": "user", "text": "Question: {{#start.input#}}\nContext: {{#context#}}"},
    ]
    assert llm_node.data.context == {
        "enabled": True,
        "variable_selector": ["retriever", "context"],
    }
    assert llm_node.data.memory == {
        "query_prompt_template": "{{#sys.query#}}",
        "role_prefix": {"assistant": "", "user": ""},
        "window": {"enabled": True, "size": 6},
    }
