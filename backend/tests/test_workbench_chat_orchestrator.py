import httpx

from core.workbench.chat_orchestrator import (
    ChatAction,
    ChatPlan,
    OpenAIChatPlanner,
    RuleBasedChatPlanner,
    WorkbenchChatOrchestrator,
    WorkflowChatContext,
)


def _context() -> WorkflowChatContext:
    return WorkflowChatContext(
        workflow_id="wf3",
        name="文档摘要生成器",
        status="pending",
        nodes=6,
        migrated=0,
        failed=0,
        score=0.0,
    )


def test_rule_based_chat_planner_builds_action_sequence() -> None:
    planner = RuleBasedChatPlanner()

    plan = planner.plan("帮我迁移当前工作流，然后生成测试并运行测试", _context())

    assert [action.type for action in plan.actions] == [
        "migrate_current",
        "generate_tests",
        "run_tests",
    ]
    assert plan.reply is None


def test_workbench_chat_orchestrator_falls_back_when_model_planner_fails() -> None:
    class BrokenPlanner:
        def plan(self, text: str, context: WorkflowChatContext) -> ChatPlan:
            del text, context
            raise RuntimeError("planner unavailable")

    orchestrator = WorkbenchChatOrchestrator(
        model_planner=BrokenPlanner(),
        fallback_planner=RuleBasedChatPlanner(),
    )

    plan = orchestrator.plan("查看当前状态", _context())

    assert [action.type for action in plan.actions] == ["report_status"]


def test_openai_chat_planner_parses_tool_call_arguments(monkeypatch) -> None:
    planner = OpenAIChatPlanner(
        api_key="test-key",
        model="gpt-4.1-mini",
        api_base="https://api.openai.com/v1",
        timeout_seconds=5.0,
    )
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "plan_workbench_actions",
                                        "arguments": (
                                            '{"actions":[{"type":"migrate_current"},{"type":"run_tests"}],'
                                            '"reply":"先迁移再执行测试。"}'
                                        ),
                                    }
                                }
                            ]
                        }
                    }
                ]
            }

    def fake_post(url: str, *, headers: dict, json: dict, timeout: float) -> FakeResponse:
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)

    plan = planner.plan("把这个流程迁移一下，然后跑一遍测试", _context())

    assert [action.type for action in plan.actions] == ["migrate_current", "run_tests"]
    assert plan.reply == "先迁移再执行测试。"
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["timeout"] == 5.0
    assert (captured["json"] or {}).get("tool_choice") == {
        "type": "function",
        "function": {"name": "plan_workbench_actions"},
    }


def test_workbench_chat_orchestrator_prefers_model_plan_when_available() -> None:
    class StubPlanner:
        def plan(self, text: str, context: WorkflowChatContext) -> ChatPlan:
            del text, context
            return ChatPlan(
                actions=[ChatAction(type="report_status")],
                reply="这是模型规划出的答复。",
            )

    orchestrator = WorkbenchChatOrchestrator(
        model_planner=StubPlanner(),
        fallback_planner=RuleBasedChatPlanner(),
    )

    plan = orchestrator.plan("随便整理一下", _context())

    assert [action.type for action in plan.actions] == ["report_status"]
    assert plan.reply == "这是模型规划出的答复。"
