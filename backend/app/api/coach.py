from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.api.dependencies import get_coach_use_cases
from app.application.use_cases.coach import CoachUseCases
from app.domain.models import CoachChatRequest, CoachChatResponse


router = APIRouter(prefix="/api/coach", tags=["coach"])


@router.post("/chat", response_model=CoachChatResponse)
def chat_with_coach(
    request: CoachChatRequest,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    session_id: Annotated[
        str,
        Header(alias="X-Session-ID", min_length=1, max_length=128),
    ],
    use_cases: Annotated[CoachUseCases, Depends(get_coach_use_cases)],
) -> CoachChatResponse:
    """
    在隔离的工作记忆会话中处理 AI 教练对话。

    :param request: 教练对话请求。
    :param user_id: 用户标识。
    :param session_id: 会话标识。
    :param use_cases: AI 教练应用用例。
    :return: AI 教练回复。
    """
    return use_cases.chat(user_id, session_id, request)
