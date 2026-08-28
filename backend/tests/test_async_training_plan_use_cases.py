import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from app.application.errors import NotFoundError
from app.application.use_cases.training_plans import TrainingPlanUseCases
from app.domain.models import TrainingPlanExplanationResponse


async def _assert_history_and_detail_use_async_repository() -> None:
    """
    验证训练计划历史和详情通过异步 Repository 查询。

    :return: 无返回值。
    """
    repository = Mock()
    repository.list_by_user = AsyncMock(return_value=[])
    repository.get_by_id_for_user = AsyncMock(return_value=None)

    use_cases = TrainingPlanUseCases(
        repository=repository,
        agent=Mock(),
        explainer=Mock(),
    )

    history = await use_cases.list_history("training-user")

    assert history.plans == []
    repository.list_by_user.assert_awaited_once_with(
        "training-user"
    )

    with pytest.raises(
        NotFoundError,
        match="Training plan not found",
    ):
        await use_cases.get_detail("training-user", 999)

    repository.get_by_id_for_user.assert_awaited_once_with(
        "training-user",
        999,
    )


async def _assert_explanation_uses_loaded_plan() -> None:
    """
    验证计划解释使用异步查询得到的正式计划。

    :return: 无返回值。
    """
    plan = Mock()
    explanation = TrainingPlanExplanationResponse(
        plan_id=7,
        summary="计划解释。",
        reasons=["符合用户目标。"],
        safety_notes=[],
    )

    repository = Mock()
    repository.get_by_id_for_user = AsyncMock(
        return_value=plan
    )
    explainer = Mock()
    explainer.explain_training_plan.return_value = explanation

    use_cases = TrainingPlanUseCases(
        repository=repository,
        agent=Mock(),
        explainer=explainer,
    )

    result = await use_cases.explain("training-user", 7)

    assert result == explanation
    repository.get_by_id_for_user.assert_awaited_once_with(
        "training-user",
        7,
    )
    explainer.explain_training_plan.assert_called_once_with(plan)


def test_history_and_detail_use_async_repository() -> None:
    """
    验证正式计划历史和详情的异步查询行为。

    :return: 无返回值。
    """
    asyncio.run(_assert_history_and_detail_use_async_repository())


def test_explanation_uses_loaded_plan() -> None:
    """
    验证正式计划解释使用已加载的计划。

    :return: 无返回值。
    """
    asyncio.run(_assert_explanation_uses_loaded_plan())