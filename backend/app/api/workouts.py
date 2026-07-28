from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.domain.models import (
    WorkoutDayDraft,
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

    plan_day = _get_plan_day(plan.plan.days, session.plan_day_index)
    _validate_logged_exercises(session, plan_day)

    return workout_session_repository.save(
        user_id=user_id,
        plan_id=plan_id,
        plan_day_name=plan_day.name,
        session=session,
        safety_alert=_build_safety_alert(session),
    )


@router.get("/history", response_model=WorkoutHistoryResponse)
def list_workout_history(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    plan_id: int | None = None,
) -> WorkoutHistoryResponse:
    return WorkoutHistoryResponse(
        sessions=workout_session_repository.list_by_user(user_id, plan_id=plan_id)
    )


def _get_plan_day(
    plan_days: list[WorkoutDayDraft],
    plan_day_index: int,
) -> WorkoutDayDraft:
    if plan_day_index > len(plan_days):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Plan day {plan_day_index} does not exist. "
                f"This plan has {len(plan_days)} days."
            ),
        )

    return plan_days[plan_day_index - 1]


def _validate_logged_exercises(
    session: WorkoutSessionCreate,
    plan_day: WorkoutDayDraft,
) -> None:
    planned_names = {
        exercise.exercise_name.casefold()
        for exercise in plan_day.exercises
    }
    unplanned_names = sorted(
        {
            workout_set.exercise_name
            for workout_set in session.sets
            if workout_set.exercise_name.casefold() not in planned_names
        }
    )
    if unplanned_names:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Workout contains exercises outside the selected plan day.",
                "unplanned_exercises": unplanned_names,
            },
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
