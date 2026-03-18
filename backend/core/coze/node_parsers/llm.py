from __future__ import annotations

from typing import Any

from core.ir.models import IRVariable
from core.ir.types import IRNodeType, IRVariableType

from . import register_parser


class LLMNodeParser:
    _SUPPORTED_PROMPT_ROLES = {"system", "user", "assistant"}

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

            prompt_messages, unsupported_roles = self._extract_prompt_messages(llm_param)
            if prompt_messages:
                config["prompt_messages"] = prompt_messages
            if unsupported_roles:
                config["unsupported_prompt_roles"] = unsupported_roles

            memory_query_prompt_template = self._first_present(
                llm_param,
                "memoryQueryPromptTemplate",
                "memory_query_prompt_template",
            )
            if memory_query_prompt_template not in (None, ""):
                config["memory_query_prompt_template"] = str(memory_query_prompt_template)

            memory_role_prefix = self._extract_memory_role_prefix(llm_param)
            if memory_role_prefix:
                config["memory_role_prefix"] = memory_role_prefix

            unsupported_settings = self._collect_unsupported_semantic_settings(llm_param)
            if unsupported_settings:
                config["unsupported_semantic_settings"] = unsupported_settings

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

    @classmethod
    def _extract_prompt_messages(cls, llm_param: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
        for key in ("promptMessages", "prompt_messages", "messages", "messageList", "message_list"):
            messages, unsupported_roles = cls._normalize_prompt_messages(llm_param.get(key))
            if messages:
                return messages, unsupported_roles

        messages: list[dict[str, str]] = []
        system_prompt = str(llm_param.get("systemPrompt") or "")
        prompt = str(llm_param.get("prompt") or "")
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})
        return messages, []

    @classmethod
    def _normalize_prompt_messages(cls, raw_messages: Any) -> tuple[list[dict[str, str]], list[str]]:
        if not isinstance(raw_messages, list):
            return [], []

        messages: list[dict[str, str]] = []
        unsupported_roles: list[str] = []
        for raw_message in raw_messages:
            if not isinstance(raw_message, dict):
                continue
            role = cls._coerce_prompt_role(raw_message)
            text = cls._coerce_prompt_text(raw_message)
            if not role:
                continue
            if role not in cls._SUPPORTED_PROMPT_ROLES:
                unsupported_roles.append(role)
                continue
            messages.append({"role": role, "text": text})
        return messages, list(dict.fromkeys(unsupported_roles))

    @staticmethod
    def _coerce_prompt_role(raw_message: dict[str, Any]) -> str:
        raw_role = (
            raw_message.get("role")
            or raw_message.get("messageType")
            or raw_message.get("message_type")
            or raw_message.get("speaker")
            or raw_message.get("author")
            or ""
        )
        normalized = str(raw_role).strip().lower().replace("-", "_")
        return {
            "system": "system",
            "sys": "system",
            "assistant": "assistant",
            "bot": "assistant",
            "model": "assistant",
            "ai": "assistant",
            "user": "user",
            "human": "user",
        }.get(normalized, normalized)

    @staticmethod
    def _coerce_prompt_text(raw_message: dict[str, Any]) -> str:
        for key in ("text", "content", "prompt", "message"):
            value = raw_message.get(key)
            if value is not None:
                return str(value)
        return ""

    @classmethod
    def _extract_memory_role_prefix(cls, llm_param: dict[str, Any]) -> dict[str, str]:
        direct_value = cls._first_present(llm_param, "memoryRolePrefix", "memory_role_prefix")
        if isinstance(direct_value, dict):
            assistant = str(direct_value.get("assistant") or "")
            user = str(direct_value.get("user") or "")
            if assistant or user:
                return {"assistant": assistant, "user": user}

        assistant = cls._first_present(
            llm_param,
            "assistantRolePrefix",
            "assistant_role_prefix",
            "memoryAssistantRolePrefix",
            "memory_assistant_role_prefix",
        )
        user = cls._first_present(
            llm_param,
            "userRolePrefix",
            "user_role_prefix",
            "memoryUserRolePrefix",
            "memory_user_role_prefix",
        )
        if assistant not in (None, "") or user not in (None, ""):
            return {"assistant": str(assistant or ""), "user": str(user or "")}
        return {}

    @classmethod
    def _collect_unsupported_semantic_settings(cls, llm_param: dict[str, Any]) -> list[str]:
        supported_keys = {
            "modelID",
            "modelId",
            "modelName",
            "modleName",
            "provider",
            "providerName",
            "resourceID",
            "resource_id",
            "temperature",
            "maxTokens",
            "topP",
            "prompt",
            "systemPrompt",
            "enableChatHistory",
            "chatHistoryRound",
            "promptMessages",
            "prompt_messages",
            "messages",
            "messageList",
            "message_list",
            "memoryQueryPromptTemplate",
            "memory_query_prompt_template",
            "memoryRolePrefix",
            "memory_role_prefix",
            "assistantRolePrefix",
            "assistant_role_prefix",
            "memoryAssistantRolePrefix",
            "memory_assistant_role_prefix",
            "userRolePrefix",
            "user_role_prefix",
            "memoryUserRolePrefix",
            "memory_user_role_prefix",
        }
        flagged: list[str] = []
        for key, value in llm_param.items():
            if key in supported_keys or not cls._has_meaningful_value(value):
                continue
            normalized = key.replace("_", "").lower()
            if any(
                token in normalized for token in ("prompt", "message", "memory", "history", "context", "roleprefix")
            ):
                flagged.append(str(key))
        return list(dict.fromkeys(flagged))

    @staticmethod
    def _has_meaningful_value(value: Any) -> bool:
        if value in (None, "", [], {}):
            return False
        return True

    @staticmethod
    def _first_present(data: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data and data[key] not in (None, ""):
                return data[key]
        return None

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
