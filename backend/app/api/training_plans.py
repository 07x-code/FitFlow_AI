from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import get_training_plan_use_cases
from app.application.use_cases.training_plans import TrainingPlanUseCases
from app.domain.models import (
    TrainingPlanDraftResponse,
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
    TrainingPlanHistoryResponse,
)


router = APIRouter(prefix="/api/training-plans", tags=["training-plans"])


@router.post(
    "/draft",
    response_model=TrainingPlanDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_training_plan_draft(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanDraftResponse:
    return use_cases.create_draft(user_id)


@router.get("/history", response_model=TrainingPlanHistoryResponse)
def list_training_plan_history(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanHistoryResponse:
    return use_cases.list_history(user_id)


@router.get("/{plan_id}", response_model=TrainingPlanHistoryItem)
def get_training_plan_detail(
    plan_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanHistoryItem:
    return use_cases.get_detail(user_id, plan_id)


@router.get("/{plan_id}/explanation", response_model=TrainingPlanExplanationResponse)
def get_training_plan_explanation(
    plan_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanExplanationResponse:
    return use_cases.explain(user_id, plan_id)
