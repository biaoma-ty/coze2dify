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

        # Prompt template — inject variable references as {{#...#}} template syntax
        prompt = config.get("prompt_template", "")
        system_prompt = config.get("system_prompt", "")

        # Replace input variable names with Dify template references in prompt text
        for inp in ir_node.inputs:
            if inp.ref:
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
        context: dict[str, Any] = {"enabled": False, "variable_selector": []}
        extra["context"] = context

        return extra


register_generator(IRNodeType.LLM, LLMNodeGenerator())
