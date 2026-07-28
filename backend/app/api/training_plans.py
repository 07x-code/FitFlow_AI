from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.domain.models import (
    TrainingPlanDraftResponse,
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
    TrainingPlanHistoryResponse,
)
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.services.coach_explainer import create_coach_explainer
from app.agents.training_plan_agent import create_training_plan_agent


router = APIRouter(prefix="/api/training-plans", tags=["training-plans"])

profile_repository = ProfileRepository()
training_plan_repository = TrainingPlanRepository()
coach_explainer = create_coach_explainer()
training_plan_agent = create_training_plan_agent(
    profile_repository=profile_repository,
    training_plan_repository=training_plan_repository,
)


@router.post(
    "/draft",
    response_model=TrainingPlanDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_training_plan_draft(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanDraftResponse:
    result = training_plan_agent.run(user_id)
    if result.response is None:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.error_detail,
        )

    return result.response


@router.get("/history", response_model=TrainingPlanHistoryResponse)
def list_training_plan_history(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanHistoryResponse:
    return TrainingPlanHistoryResponse(
        plans=training_plan_repository.list_by_user(user_id)
    )


@router.get("/{plan_id}", response_model=TrainingPlanHistoryItem)
def get_training_plan_detail(
    plan_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanHistoryItem:
    plan = training_plan_repository.get_by_id_for_user(user_id, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Training plan not found.")

    return plan


@router.get("/{plan_id}/explanation", response_model=TrainingPlanExplanationResponse)
def get_training_plan_explanation(
    plan_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanExplanationResponse:
    plan = training_plan_repository.get_by_id_for_user(user_id, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Training plan not found.")

    return coach_explainer.explain_training_plan(plan)
