import asyncio
from unittest.mock import AsyncMock

from app.ai.agents.single.coach import create_coach_agent
from app.ai.agents.single.planner import create_training_plan_agent
from app.ai.tools.fitness import (
    ASSESS_RISK_TOOL,
    GENERATE_TRAINING_PLAN_TOOL,
    GET_PROFILE_TOOL,
    VALIDATE_TRAINING_PLAN_TOOL,
)
from app.domain.models import CoachChatRequest, FitnessProfileCreate
from app.infrastructure.knowledge.retriever import KnowledgeRetriever
from app.infrastructure.llm.provider import FakeLLMProvider
from app.infrastructure.memory.in_memory import InMemoryWorkingMemoryStore


def build_profile(
    *,
    health_flags: list[str] | None = None,
) -> FitnessProfileCreate:
    """
    创建 Agent 测试使用的用户画像。

    :param health_flags: 可选的健康风险标记。
    :return: 测试用户画像。
    """
    return FitnessProfileCreate(
        age=22,
        sex="male",
        height_cm=175,
        weight_kg=70,
        goal="muscle_gain",
        sessions_per_week=3,
        session_minutes=60,
        health_flags=health_flags or [],
    )


def test_training_plan_agent_exposes_deterministic_steps_as_tools() -> None:
    """
    验证 Planner 只暴露确定性训练计划工具。

    :return: 无返回值。
    """
    agent = create_training_plan_agent(
        profile_repository=AsyncMock(),
    )

    assert agent.tool_registry.names() == (
        GET_PROFILE_TOOL,
        ASSESS_RISK_TOOL,
        GENERATE_TRAINING_PLAN_TOOL,
        VALIDATE_TRAINING_PLAN_TOOL,
    )


def test_training_plan_agent_returns_validated_safe_draft() -> None:
    """
    验证 Planner 为低风险画像返回安全草案。

    :return: 无返回值。
    """
    profiles = AsyncMock()
    profiles.get.return_value = build_profile()
    agent = create_training_plan_agent(
        profile_repository=profiles,
    )

    result = asyncio.run(agent.run("safe-user"))

    assert result.status_code == 201
    assert result.response is not None
    assert result.response.safety_check.valid is True
    profiles.get.assert_awaited_once_with("safe-user")


def test_coach_agent_blocks_risky_profile_before_optional_tools() -> None:
    """
    验证高风险画像在读取可选上下文前被安全规则阻断。

    :return: 无返回值。
    """
    profiles = AsyncMock()
    plans = AsyncMock()
    memories = AsyncMock()
    working_memory = InMemoryWorkingMemoryStore()
    profiles.get.return_value = build_profile(
        health_flags=["chest_pain"]
    )

    agent = create_coach_agent(
        profile_repository=profiles,
        training_plan_repository=plans,
        memory_repository=memories,
        knowledge_retriever=KnowledgeRetriever.from_default_file(),
        llm_provider=FakeLLMProvider(),
        working_memory=working_memory,
    )

    response = asyncio.run(
        agent.chat(
            "blocked-user",
            "blocked-session",
            CoachChatRequest(message="Can I train today?"),
        )
    )

    assert response is not None
    assert response.safety_level == "blocked"
    assert response.referenced_plan_id is None
    profiles.get.assert_awaited_once_with("blocked-user")
    plans.list_by_user.assert_not_awaited()
    memories.list_by_user.assert_not_awaited()
    assert {
        item.kind
        for item in working_memory.list(
            "blocked-user",
            "blocked-session",
        )
    } == {"message", "tool_observation"}