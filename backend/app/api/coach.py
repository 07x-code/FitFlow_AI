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
    use_cases: Annotated[CoachUseCases, Depends(get_coach_use_cases)],
) -> CoachChatResponse:
    return use_cases.chat(user_id, request)
