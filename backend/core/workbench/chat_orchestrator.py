from __future__ import annotations

import json
import logging
from typing import Any, Literal, Protocol

import httpx
from pydantic import BaseModel, Field

from config import settings

logger = logging.getLogger(__name__)

ActionType = Literal[
    "migrate_current",
    "batch_migrate",
    "generate_tests",
    "run_tests",
    "report_status",
]


class WorkflowChatContext(BaseModel):
    workflow_id: str
    name: str
    status: str
    nodes: int
    migrated: int
    failed: int
    score: float


class ChatAction(BaseModel):
    type: ActionType


class ChatPlan(BaseModel):
    actions: list[ChatAction] = Field(default_factory=list)
    reply: str | None = None


class ChatPlanner(Protocol):
    def plan(self, text: str, context: WorkflowChatContext) -> ChatPlan: ...


class RuleBasedChatPlanner:
    def plan(self, text: str, context: WorkflowChatContext) -> ChatPlan:
        del context

        normalized = self._normalize(text)
        wants_migrate = any(keyword in normalized for keyword in ("迁移", "migrate", "convert"))
        wants_help = any(keyword in normalized for keyword in ("帮助", "help", "能做什么", "支持什么"))
        wants_status = any(keyword in normalized for keyword in ("状态", "进展", "概况", "status"))
        wants_generate = any(
            keyword in normalized for keyword in ("生成测试", "生成用例", "创建测试", "创建用例", "补测试", "补用例")
        )
        wants_run_tests = any(
            keyword in normalized for keyword in ("运行测试", "执行测试", "跑测试", "test", "测试一下", "测一下")
        )
        if not wants_run_tests and ("测试" in normalized or "用例" in normalized) and not wants_generate:
            wants_run_tests = True
        wants_batch = any(keyword in normalized for keyword in ("批量", "全部", "所有", "all"))

        if wants_help:
            return ChatPlan(reply="可用指令: 迁移当前工作流, 批量迁移, 生成测试, 运行测试, 迁移并运行测试, 查看状态。")

        actions: list[ChatAction] = []
        if wants_migrate:
            actions.append(ChatAction(type="batch_migrate" if wants_batch else "migrate_current"))
        if wants_generate:
            actions.append(ChatAction(type="generate_tests"))
        if wants_run_tests:
            actions.append(ChatAction(type="run_tests"))
        if wants_status and not actions:
            actions.append(ChatAction(type="report_status"))

        return ChatPlan(actions=self._dedupe_actions(actions))

    @staticmethod
    def _normalize(text: str) -> str:
        return "".join(char for char in text.lower() if not char.isspace())

    @staticmethod
    def _dedupe_actions(actions: list[ChatAction]) -> list[ChatAction]:
        seen: set[str] = set()
        ordered: list[ChatAction] = []
        for action in actions:
            if action.type in seen:
                continue
            seen.add(action.type)
            ordered.append(action)
        return ordered


class OpenAIChatPlanner:
    _TOOL_NAME = "plan_workbench_actions"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        api_base: str = "https://api.openai.com/v1",
        timeout_seconds: float = 15.0,
    ) -> None:
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.api_base = api_base.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls) -> OpenAIChatPlanner | None:
        if not settings.workbench_chat_api_key.strip() or not settings.workbench_chat_model.strip():
            return None
        return cls(
            api_key=settings.workbench_chat_api_key,
            model=settings.workbench_chat_model,
            api_base=settings.workbench_chat_api_base,
            timeout_seconds=settings.workbench_chat_timeout_seconds,
        )

    def plan(self, text: str, context: WorkflowChatContext) -> ChatPlan:
        response = httpx.post(
            f"{self.api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a coze2dify Migration Workbench sandbox planner. "
                            "Decide whether the user wants to trigger one or more workbench actions. "
                            "Use only these actions: migrate_current, batch_migrate, generate_tests, "
                            "run_tests, report_status. "
                            "If the message is ordinary sandbox conversation and should still go to the "
                            "Coze/Dify comparison path, return no actions and reply as null. "
                            "If the user asks what the tool can do, return no actions and a short reply."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "message": text,
                                "workflow": context.model_dump(),
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": self._TOOL_NAME,
                            "description": "Plan migration workbench actions for the current sandbox message.",
                            "parameters": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "actions": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": False,
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "enum": [
                                                        "migrate_current",
                                                        "batch_migrate",
                                                        "generate_tests",
                                                        "run_tests",
                                                        "report_status",
                                                    ],
                                                }
                                            },
                                            "required": ["type"],
                                        },
                                    },
                                    "reply": {
                                        "type": ["string", "null"],
                                    },
                                },
                                "required": ["actions", "reply"],
                            },
                        },
                    }
                ],
                "tool_choice": {
                    "type": "function",
                    "function": {"name": self._TOOL_NAME},
                },
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        arguments = self._extract_tool_arguments(payload)
        plan = ChatPlan.model_validate_json(arguments)
        plan.actions = RuleBasedChatPlanner._dedupe_actions(plan.actions)
        return plan

    def _extract_tool_arguments(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("Missing choices in chat completion response")

        message = (choices[0] or {}).get("message") or {}
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            function_payload = (tool_calls[0] or {}).get("function") or {}
            arguments = function_payload.get("arguments")
            if isinstance(arguments, str) and arguments.strip():
                return arguments

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                    return str(item["text"])

        raise ValueError("Missing tool arguments in chat completion response")


class WorkbenchChatOrchestrator:
    def __init__(
        self,
        *,
        model_planner: ChatPlanner | None = None,
        fallback_planner: ChatPlanner | None = None,
    ) -> None:
        self._model_planner = model_planner if model_planner is not None else OpenAIChatPlanner.from_settings()
        self._fallback_planner = fallback_planner or RuleBasedChatPlanner()

    def plan(self, text: str, context: WorkflowChatContext) -> ChatPlan:
        if self._model_planner is not None:
            try:
                plan = self._model_planner.plan(text, context)
                if plan.actions or plan.reply:
                    return plan
            except Exception as exc:  # noqa: BLE001 - chat orchestration should degrade gracefully
                logger.warning("Workbench chat planner failed, falling back to rules: %s", exc)
        return self._fallback_planner.plan(text, context)
