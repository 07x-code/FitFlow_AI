from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.domain.models import (
    SafetyCheckResult,
    TrainingPlanDraftResponse,
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
    TrainingPlanHistoryResponse,
)
from app.domain.plan_explainer import explain_training_plan
from app.domain.plan_generator import generate_beginner_plan
from app.domain.risk_rules import assess_risk
from app.domain.training_rules import validate_beginner_plan
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository


router = APIRouter(prefix="/api/training-plans", tags=["training-plans"])

profile_repository = ProfileRepository()
training_plan_repository = TrainingPlanRepository()


@router.post(
    "/draft",
    response_model=TrainingPlanDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_training_plan_draft(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanDraftResponse:
    profile = profile_repository.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    risk = assess_risk(profile)
    if risk["can_auto_plan"] is False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Automatic plan generation is blocked.",
                "risk": risk,
            },
        )

    plan = generate_beginner_plan(profile)
    safety_check = SafetyCheckResult.model_validate(validate_beginner_plan(plan))
    if safety_check.valid is False:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Generated plan failed safety check.",
                "safety_check": safety_check.model_dump(),
            },
        )

    training_plan_repository.save(user_id, plan, safety_check)
    return TrainingPlanDraftResponse(plan=plan, safety_check=safety_check)


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

    return explain_training_plan(plan)
