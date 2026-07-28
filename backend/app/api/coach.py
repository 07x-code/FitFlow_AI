from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from app.domain.models import CoachChatRequest, CoachChatResponse
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.agents.coach_agent import create_coach_agent


router = APIRouter(prefix="/api/coach", tags=["coach"])

profile_repository = ProfileRepository()
training_plan_repository = TrainingPlanRepository()
coach_agent = create_coach_agent(
    profile_repository=profile_repository,
    training_plan_repository=training_plan_repository,
)


@router.post("/chat", response_model=CoachChatResponse)
def chat_with_coach(
    request: CoachChatRequest,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> CoachChatResponse:
    response = coach_agent.chat(user_id, request)
    if response is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return response
