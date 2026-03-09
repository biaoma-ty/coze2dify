from __future__ import annotations

from typing import Any

from core.ir.models import IRVariable
from core.ir.types import IRNodeType, IRVariableType

from . import register_parser


class LLMNodeParser:
    def parse(self, node: Any, variable_resolver: Any) -> dict[str, Any]:
        config: dict[str, Any] = {}
        outputs: list[IRVariable] = []

        data = node.data or {}
        coze_inputs = data.get("inputs", {})

        llm_param = coze_inputs.get("llmParam", {})
        if llm_param:
            config["model"] = llm_param.get("modelID", "")
            config["temperature"] = llm_param.get("temperature", 0.7)
            config["max_tokens"] = llm_param.get("maxTokens", 4096)
            config["top_p"] = llm_param.get("topP", 1.0)
            config["prompt_template"] = llm_param.get("prompt", "")
            system_prompt = llm_param.get("systemPrompt", "")
            if system_prompt:
                config["system_prompt"] = system_prompt

        outputs.append(IRVariable(name="output", var_type=IRVariableType.STRING))
        return {"outputs": outputs, "config": config}


register_parser(IRNodeType.LLM, LLMNodeParser())
