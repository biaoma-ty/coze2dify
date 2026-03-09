from __future__ import annotations

from typing import Any

from core.ir.types import IRNodeType

from . import register_generator


class LLMNodeGenerator:
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]:
        config = ir_node.config
        extra: dict[str, Any] = {}

        # Model config
        extra["model"] = {
            "provider": "",
            "name": config.get("model", ""),
            "mode": "chat",
            "completion_params": {
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 4096),
                "top_p": config.get("top_p", 1.0),
            },
        }

        # Prompt template
        prompt = config.get("prompt_template", "")
        system_prompt = config.get("system_prompt", "")

        prompts = []
        if system_prompt:
            prompts.append({"role": "system", "text": system_prompt})
        prompts.append({"role": "user", "text": prompt})
        extra["prompt_template"] = prompts

        # Transform variable references in inputs
        for inp in ir_node.inputs:
            if inp.ref:
                selector = var_transformer.to_selector(inp.ref)
                extra.setdefault("variable_selector", []).append(selector)

        return extra


register_generator(IRNodeType.LLM, LLMNodeGenerator())
