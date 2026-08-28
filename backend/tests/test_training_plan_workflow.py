import asyncio
from unittest.mock import AsyncMock

from app.ai.agents.single.planner import create_training_plan_agent
from app.domain.models import FitnessProfileCreate


def build_profile(
    *,
    health_flags: list[str] | None = None,
) -> FitnessProfileCreate:
    """
    创建训练计划工作流测试使用的用户画像。

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


def test_training_plan_workflow_returns_validated_safe_draft() -> None:
    """
    验证低风险画像可以生成通过安全检查的训练计划草案。

    :return: 无返回值。
    """
    profiles = AsyncMock()
    profiles.get.return_value = build_profile()
    workflow = create_training_plan_agent(
        profile_repository=profiles,
    )

    result = asyncio.run(workflow.run("safe-workflow-user"))

    assert result.status_code == 201
    assert result.response is not None
    assert len(result.response.plan.days) == 3
    assert result.response.safety_check.valid is True
    profiles.get.assert_awaited_once_with("safe-workflow-user")


def test_training_plan_workflow_blocks_risky_profile_before_generation() -> None:
    """
    验证高风险画像会在计划生成前被安全规则阻断。

    :return: 无返回值。
    """
    profiles = AsyncMock()
    profiles.get.return_value = build_profile(
        health_flags=["chest_pain"]
    )
    workflow = create_training_plan_agent(
        profile_repository=profiles,
    )

    result = asyncio.run(workflow.run("risky-workflow-user"))

    assert result.status_code == 409
    assert result.response is None
    assert result.error_detail == {
        "message": "Automatic plan generation is blocked.",
        "risk": {
            "level": "blocked",
            "can_auto_plan": False,
        },
    }
    profiles.get.assert_awaited_once_with("risky-workflow-user")