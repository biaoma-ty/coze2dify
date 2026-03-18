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

        context_selector, replacements = self._build_template_replacements(ir_node, var_transformer)
        prompt_messages = self._build_prompt_messages(config)
        extra["prompt_template"] = [
            {
                "role": str(message.get("role") or "user"),
                "text": self._interpolate_text(str(message.get("text") or ""), replacements),
            }
            for message in prompt_messages
        ]

        # Dify LLM nodes use context for variable bindings
        context: dict[str, Any] = {"enabled": bool(context_selector), "variable_selector": context_selector}
        extra["context"] = context
        extra["memory"] = {
            "query_prompt_template": self._interpolate_text(
                str(config.get("memory_query_prompt_template", "{{#sys.query#}}")),
                replacements,
            ),
            "role_prefix": deepcopy(config.get("memory_role_prefix", {"assistant": "", "user": ""})),
            "window": {
                "enabled": bool(config.get("enable_chat_history", False)),
                "size": int(config.get("chat_history_round", 10) or 10),
            },
        }

        return extra

    @staticmethod
    def _build_prompt_messages(config: dict[str, Any]) -> list[dict[str, str]]:
        raw_messages = config.get("prompt_messages")
        if isinstance(raw_messages, list) and raw_messages:
            return [
                {
                    "role": str(message.get("role") or "user"),
                    "text": str(message.get("text") or ""),
                }
                for message in raw_messages
                if isinstance(message, dict)
            ]

        messages: list[dict[str, str]] = []
        system_prompt = str(config.get("system_prompt") or "")
        prompt = str(config.get("prompt_template") or "")
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})
        return messages

    @staticmethod
    def _build_template_replacements(ir_node: Any, var_transformer: Any) -> tuple[list[str], dict[str, str]]:
        context_selector: list[str] = []
        replacements: dict[str, str] = {}
        for inp in ir_node.inputs:
            if not inp.name:
                continue
            if inp.ref:
                if inp.name.lower() == "context":
                    context_selector = var_transformer.to_selector(inp.ref)
                    replacement = "{{#context#}}"
                else:
                    replacement = var_transformer.to_template(inp.ref)
            elif inp.literal_value is not None:
                replacement = str(inp.literal_value)
            else:
                replacement = ""
            replacements["{{" + inp.name + "}}"] = replacement
            replacements["{" + inp.name + "}"] = replacement
        return context_selector, replacements

    @staticmethod
    def _interpolate_text(text: str, replacements: dict[str, str]) -> str:
        rendered = text
        for placeholder, replacement in replacements.items():
            rendered = rendered.replace(placeholder, replacement)
        return rendered


register_generator(IRNodeType.LLM, LLMNodeGenerator())
