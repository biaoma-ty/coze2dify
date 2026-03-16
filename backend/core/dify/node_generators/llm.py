from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.ir.types import IRNodeType

from . import register_generator


class LLMNodeGenerator:
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]:
        config = ir_node.config
        extra: dict[str, Any] = {}

        # Model config
        extra["model"] = {
            "provider": config.get("model_provider", ""),
            "name": config.get("model", ""),
            "mode": "chat",
            "completion_params": {
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 4096),
                "top_p": config.get("top_p", 1.0),
            },
        }

        # Prompt template — inject variable references as {{#...#}} template syntax
        prompt = config.get("prompt_template", "")
        system_prompt = config.get("system_prompt", "")
        context_selector: list[str] = []

        # Replace input variable names with Dify template references in prompt text
        for inp in ir_node.inputs:
            if inp.ref:
                if inp.name and inp.name.lower() == "context":
                    context_selector = var_transformer.to_selector(inp.ref)
                    template_ref = "{{#context#}}"
                else:
                    template_ref = var_transformer.to_template(inp.ref)
                # Replace {{name}} or {name} placeholders with Dify template syntax
                if inp.name:
                    prompt = prompt.replace("{{" + inp.name + "}}", template_ref)
                    prompt = prompt.replace("{" + inp.name + "}", template_ref)
                    system_prompt = system_prompt.replace("{{" + inp.name + "}}", template_ref)
                    system_prompt = system_prompt.replace("{" + inp.name + "}", template_ref)

        prompts = []
        if system_prompt:
            prompts.append({"role": "system", "text": system_prompt})
        prompts.append({"role": "user", "text": prompt})
        extra["prompt_template"] = prompts

        # Dify LLM nodes use context for variable bindings
        context: dict[str, Any] = {"enabled": bool(context_selector), "variable_selector": context_selector}
        extra["context"] = context
        extra["memory"] = {
            "query_prompt_template": config.get("memory_query_prompt_template", "{{#sys.query#}}"),
            "role_prefix": deepcopy(config.get("memory_role_prefix", {"assistant": "", "user": ""})),
            "window": {
                "enabled": bool(config.get("enable_chat_history", False)),
                "size": int(config.get("chat_history_round", 10) or 10),
            },
        }

        return extra


register_generator(IRNodeType.LLM, LLMNodeGenerator())
