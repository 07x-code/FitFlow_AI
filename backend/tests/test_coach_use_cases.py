import asyncio
from unittest.mock import AsyncMock

import pytest

from app.application.errors import NotFoundError
from app.application.use_cases.coach import CoachUseCases
from app.domain.models import CoachChatRequest, CoachChatResponse


def test_coach_use_cases_awaits_agent_response() -> None:
    """
    验证 Coach 用例等待 Agent 并返回对话响应。

    :return: 无返回值。
    """
    expected = CoachChatResponse(
        answer="保持动作稳定。",
        safety_level="low",
    )
    agent = AsyncMock()
    agent.chat.return_value = expected
    use_cases = CoachUseCases(agent)

    request = CoachChatRequest(message="今天怎么训练？")
    response = asyncio.run(
        use_cases.chat(
            "coach-user",
            "coach-session",
            request,
        )
    )

    assert response == expected
    agent.chat.assert_awaited_once_with(
        "coach-user",
        "coach-session",
        request,
    )


def test_coach_use_cases_reports_missing_profile() -> None:
    """
    验证用户画像不存在时返回应用层未找到错误。

    :return: 无返回值。
    """
    agent = AsyncMock()
    agent.chat.return_value = None
    use_cases = CoachUseCases(agent)

    with pytest.raises(NotFoundError, match="Profile not found"):
        asyncio.run(
            use_cases.chat(
                "missing-user",
                "missing-session",
                CoachChatRequest(message="今天怎么训练？"),
            )
        )