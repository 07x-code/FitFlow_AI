from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.domain.models import (
    WorkoutHistoryResponse,
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
)
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.infrastructure.workout_repository import WorkoutSessionRepository


router = APIRouter(prefix="/api/workouts", tags=["workouts"])

training_plan_repository = TrainingPlanRepository()
workout_session_repository = WorkoutSessionRepository()


@router.post(
    "/{plan_id}/sessions",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workout_session(
    plan_id: int,
    session: WorkoutSessionCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> WorkoutSessionResponse:
    plan = training_plan_repository.get_by_id_for_user(user_id, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Training plan not found.")

    return workout_session_repository.save(
        user_id=user_id,
        plan_id=plan_id,
        session=session,
        safety_alert=_build_safety_alert(session),
    )


@router.get("/history", response_model=WorkoutHistoryResponse)
def list_workout_history(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> WorkoutHistoryResponse:
    return WorkoutHistoryResponse(
        sessions=workout_session_repository.list_by_user(user_id)
    )


def _build_safety_alert(
    session: WorkoutSessionCreate,
) -> WorkoutSafetyAlert | None:
    if session.pain_level >= 7 or session.fatigue_level >= 9:
        return WorkoutSafetyAlert(
            level="caution",
            message=(
                "本次反馈显示疼痛或疲劳偏高，请暂停加量，必要时停止训练并咨询专业人士。"
            ),
        )

    return None
