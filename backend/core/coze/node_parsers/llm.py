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

        llm_param = self._normalize_llm_param(coze_inputs.get("llmParam", {}))
        if llm_param:
            model_name = (
                llm_param.get("modelID")
                or llm_param.get("modelId")
                or llm_param.get("modelName")
                or llm_param.get("modleName")
                or ""
            )
            if model_name:
                config["model"] = str(model_name)

            provider_name = llm_param.get("provider") or llm_param.get("providerName") or ""
            if provider_name:
                config["model_provider"] = str(provider_name)

            resource_id = llm_param.get("resourceID") or llm_param.get("resource_id") or ""
            if resource_id:
                config["model_resource_id"] = str(resource_id)

            config["temperature"] = self._coerce_float(llm_param.get("temperature"), 0.7)
            config["max_tokens"] = self._coerce_int(llm_param.get("maxTokens"), 4096)
            config["top_p"] = self._coerce_float(llm_param.get("topP"), 1.0)
            config["prompt_template"] = str(llm_param.get("prompt") or "")
            system_prompt = str(llm_param.get("systemPrompt") or "")
            if system_prompt:
                config["system_prompt"] = system_prompt

            config["enable_chat_history"] = self._coerce_bool(llm_param.get("enableChatHistory"), False)
            config["chat_history_round"] = self._coerce_int(llm_param.get("chatHistoryRound"), 10)

        outputs.append(IRVariable(name="output", var_type=IRVariableType.STRING))
        return {"outputs": outputs, "config": config}

    @staticmethod
    def _normalize_llm_param(raw_param: Any) -> dict[str, Any]:
        if isinstance(raw_param, dict):
            return dict(raw_param)

        if not isinstance(raw_param, list):
            return {}

        normalized: dict[str, Any] = {}
        for item in raw_param:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            value = item.get("input", {}).get("value", {}) if isinstance(item.get("input"), dict) else {}
            if isinstance(value, dict):
                normalized[name] = value.get("content")
            else:
                normalized[name] = value
        return normalized

    @staticmethod
    def _coerce_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    @staticmethod
    def _coerce_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


register_parser(IRNodeType.LLM, LLMNodeParser())
