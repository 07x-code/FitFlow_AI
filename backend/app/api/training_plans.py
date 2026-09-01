from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user_id, get_training_plan_use_cases
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
async def create_training_plan_draft(
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanDraftResponse:
    return await use_cases.create_draft(user_id)


@router.get("/history", response_model=TrainingPlanHistoryResponse)
async def list_training_plan_history(
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanHistoryResponse:
    return await use_cases.list_history(user_id)


@router.get("/{plan_id}", response_model=TrainingPlanHistoryItem)
async def get_training_plan_detail(
    plan_id: int,
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanHistoryItem:
    return await use_cases.get_detail(user_id, plan_id)


@router.get("/{plan_id}/explanation", response_model=TrainingPlanExplanationResponse)
async def get_training_plan_explanation(
    plan_id: int,
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_cases: Annotated[
        TrainingPlanUseCases,
        Depends(get_training_plan_use_cases),
    ],
) -> TrainingPlanExplanationResponse:
    return await use_cases.explain(user_id, plan_id)
