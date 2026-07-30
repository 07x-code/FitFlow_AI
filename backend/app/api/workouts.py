from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import get_workout_use_cases
from app.application.use_cases.workouts import WorkoutUseCases
from app.domain.models import (
    WorkoutHistoryResponse,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
)


router = APIRouter(prefix="/api/workouts", tags=["workouts"])


@router.post(
    "/{plan_id}/sessions",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workout_session(
    plan_id: int,
    session: WorkoutSessionCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[WorkoutUseCases, Depends(get_workout_use_cases)],
) -> WorkoutSessionResponse:
    return use_cases.create_session(user_id, plan_id, session)


@router.get("/history", response_model=WorkoutHistoryResponse)
def list_workout_history(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[WorkoutUseCases, Depends(get_workout_use_cases)],
    plan_id: int | None = None,
) -> WorkoutHistoryResponse:
    return use_cases.list_history(user_id, plan_id)
