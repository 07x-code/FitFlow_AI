from app.ai.agents.single.coach import create_coach_agent
from app.ai.orchestration.coach_tool_graph import create_coach_tool_graph
from app.ai.tools.coach import (
    CoachReadOnlyToolExecutor,
    CoachToolRuntime,
)
from app.ai.tools.fitness import (
    GET_LATEST_TRAINING_PLAN_TOOL,
    RECALL_USER_MEMORY_TOOL,
    RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
)
from app.ai.tools.registry import ToolRegistry
from app.domain.models import CoachChatRequest, FitnessProfileCreate
from app.infrastructure.knowledge.retriever import KnowledgeRetriever
from app.infrastructure.llm.provider import FakeLLMProvider
from app.infrastructure.memory.in_memory import InMemoryWorkingMemoryStore
from app.infrastructure.persistence.sqlite.profile_repository import (
    ProfileRepository,
)
from app.infrastructure.persistence.sqlite.training_plan_repository import (
    TrainingPlanRepository,
)
from app.infrastructure.persistence.sqlite.user_memory_repository import (
    UserMemoryRepository,
)
from app.ports.llm import (
    LLMCompletion,
    LLMMessage,
    LLMToolCall,
    LLMToolCompletion,
    LLMToolDefinition,
)


def test_tool_definitions_hide_runtime_identity():
    """
    验证模型可见工具定义不包含可信运行时身份。

    :return: 无返回值。
    """
    executor = CoachReadOnlyToolExecutor(ToolRegistry())

    definitions = executor.definitions()
    serialized = repr(definitions)

    assert {definition.name for definition in definitions} == {
        GET_LATEST_TRAINING_PLAN_TOOL,
        RECALL_USER_MEMORY_TOOL,
        RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
    }
    assert "user_id" not in serialized
    assert "session_id" not in serialized


def test_runtime_user_id_is_injected_and_model_cannot_override_it():
    """
    验证后端注入用户身份且模型额外参数会被拒绝。

    :return: 无返回值。
    """
    captured_user_ids: list[str] = []
    registry = ToolRegistry()
    registry.register_function(
        name=GET_LATEST_TRAINING_PLAN_TOOL,
        description="测试读取最近训练计划。",
        function=lambda user_id: captured_user_ids.append(user_id),
    )
    executor = CoachReadOnlyToolExecutor(registry)
    runtime = CoachToolRuntime(
        user_id="trusted-user",
        session_id="trusted-session",
    )

    valid_result = executor.execute(
        LLMToolCall(
            id="valid-call",
            name=GET_LATEST_TRAINING_PLAN_TOOL,
            arguments={},
        ),
        runtime,
    )
    rejected_result = executor.execute(
        LLMToolCall(
            id="malicious-call",
            name=GET_LATEST_TRAINING_PLAN_TOOL,
            arguments={"user_id": "other-user"},
        ),
        runtime,
    )

    assert valid_result.success is True
    assert rejected_result.success is False
    assert captured_user_ids == ["trusted-user"]


def test_simple_greeting_does_not_prefetch_optional_context(tmp_path):
    """
    验证普通问候不会预先读取可选业务数据。

    :param tmp_path: Pytest 提供的临时目录。
    :return: 无返回值。
    """
    db_path = tmp_path / "fitflow.db"
    profiles = ProfileRepository(db_path)
    working_memory = InMemoryWorkingMemoryStore()
    profiles.save(
        "greeting-user",
        FitnessProfileCreate(
            age=22,
            sex="male",
            height_cm=175,
            weight_kg=70,
            goal="muscle_gain",
            sessions_per_week=3,
            session_minutes=60,
            health_flags=[],
        ),
    )
    agent = create_coach_agent(
        profile_repository=profiles,
        training_plan_repository=TrainingPlanRepository(db_path),
        memory_repository=UserMemoryRepository(db_path),
        knowledge_retriever=KnowledgeRetriever.from_default_file(),
        llm_provider=FakeLLMProvider(),
        working_memory=working_memory,
    )

    response = agent.chat(
        "greeting-user",
        "greeting-session",
        CoachChatRequest(message="你好"),
    )

    assert response is not None
    observations = {
        item.tool_name
        for item in working_memory.list(
            "greeting-user",
            "greeting-session",
        )
        if item.kind == "tool_observation"
    }
    assert GET_LATEST_TRAINING_PLAN_TOOL not in observations
    assert RECALL_USER_MEMORY_TOOL not in observations
    assert RETRIEVE_FITNESS_KNOWLEDGE_TOOL not in observations


class LoopingLLMProvider:
    """始终请求同一工具的调用上限测试替身。"""

    name = "looping"
    model = "looping-test-model"

    def __init__(self) -> None:
        """
        初始化调用计数器。

        :return: 无返回值。
        """
        self.call_count = 0

    def complete(self, prompt: str) -> LLMCompletion:
        """
        返回未使用的普通补全结果。

        :param prompt: 普通补全提示词。
        :return: 固定测试结果。
        """
        return LLMCompletion(
            content=prompt,
            provider=self.name,
            model=self.model,
        )

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: tuple[LLMToolDefinition, ...],
    ) -> LLMToolCompletion:
        """
        无论是否提供工具都重复请求读取训练计划。

        :param messages: 当前消息列表。
        :param tools: 当前工具定义。
        :return: 固定的重复工具调用。
        """
        del messages, tools
        self.call_count += 1
        return LLMToolCompletion(
            content=None,
            tool_calls=(
                LLMToolCall(
                    id=f"loop-{self.call_count}",
                    name=GET_LATEST_TRAINING_PLAN_TOOL,
                    arguments={},
                ),
            ),
            provider=self.name,
            model=self.model,
        )


def test_graph_stops_repeated_tool_calls_at_configured_limit():
    """
    验证工具调用图会在配置轮数处停止重复调用。

    :return: 无返回值。
    """
    registry = ToolRegistry()
    registry.register_function(
        name=GET_LATEST_TRAINING_PLAN_TOOL,
        description="测试读取最近训练计划。",
        function=lambda user_id: None,
    )
    provider = LoopingLLMProvider()
    graph = create_coach_tool_graph(
        llm_provider=provider,
        tool_executor=CoachReadOnlyToolExecutor(registry),
        max_tool_iterations=2,
    )

    result = graph.invoke(
        {
            "messages": [LLMMessage(role="user", content="重复调用测试")],
            "user_id": "limit-user",
            "session_id": "limit-session",
            "tool_iterations": 0,
            "pending_tool_calls": (),
            "tool_executions": [],
            "knowledge_items": [],
            "referenced_plan_id": None,
        }
    )

    assert result["tool_iterations"] == 2
    assert len(result["tool_executions"]) == 2
    assert result["pending_tool_calls"] == ()
    assert "达到上限" in result["final_answer"]
