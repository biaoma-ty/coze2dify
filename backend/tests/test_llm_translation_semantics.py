from __future__ import annotations

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator

from .semantic_oracles import llm_canvas_with_list_params, llm_canvas_with_ordered_messages_and_memory


def test_llm_parser_accepts_real_coze_list_style_parameters() -> None:
    workflow = CozeParser().parse_dict(llm_canvas_with_list_params())
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
    workflow = CozeParser().parse_dict(llm_canvas_with_list_params())
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


def test_llm_generator_preserves_message_order_literal_bindings_and_memory_templates() -> None:
    workflow = CozeParser().parse_dict(llm_canvas_with_ordered_messages_and_memory())
    llm_node = workflow.nodes[2]
    dsl = DifyGenerator().generate(workflow)
    generated_llm = next(node for node in dsl.workflow.graph.nodes if node.id == "llm")

    assert llm_node.config["prompt_messages"] == [
        {"role": "system", "text": "Persona: {{persona}}"},
        {"role": "assistant", "text": "Retrieved: {{context}}"},
        {"role": "user", "text": "Question: {{input}}"},
    ]
    assert llm_node.config["memory_query_prompt_template"] == "Recall the latest user request: {{input}}"
    assert llm_node.config["memory_role_prefix"] == {"assistant": "Dify", "user": "User"}

    assert generated_llm.data.prompt_template == [
        {"role": "system", "text": "Persona: Grounded analyst"},
        {"role": "assistant", "text": "Retrieved: {{#context#}}"},
        {"role": "user", "text": "Question: {{#start.input#}}"},
    ]
    assert generated_llm.data.context == {
        "enabled": True,
        "variable_selector": ["retriever", "context"],
    }
    assert generated_llm.data.memory == {
        "query_prompt_template": "Recall the latest user request: {{#start.input#}}",
        "role_prefix": {"assistant": "Dify", "user": "User"},
        "window": {"enabled": True, "size": 4},
    }
