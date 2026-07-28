from typing import Annotated

from fastapi import APIRouter, Header

from app.domain.models import (
    SafetyCheckResult,
    TrainingPlanDraft,
    WeeklyReportMetrics,
    WeeklyReportResponse,
    WorkoutSessionResponse,
)
from app.domain.training_rules import validate_beginner_plan
from app.infrastructure.proposal_repository import TrainingPlanProposalRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.infrastructure.workout_repository import WorkoutSessionRepository


router = APIRouter(prefix="/api/reports", tags=["reports"])

training_plan_repository = TrainingPlanRepository()
workout_session_repository = WorkoutSessionRepository()
proposal_repository = TrainingPlanProposalRepository()


@router.post("/weekly", response_model=WeeklyReportResponse)
def create_weekly_report(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> WeeklyReportResponse:
    sessions = workout_session_repository.list_by_user(user_id)
    metrics = _build_weekly_metrics(sessions)

    if _needs_lower_intensity(metrics):
        latest_plan = _get_latest_plan(user_id)
        if latest_plan is not None:
            adjusted_plan = _lower_plan_intensity(latest_plan.plan)
            safety_check = SafetyCheckResult.model_validate(
                validate_beginner_plan(adjusted_plan)
            )
            proposal = proposal_repository.create(
                user_id=user_id,
                plan=adjusted_plan,
                safety_check=safety_check,
            )
            return WeeklyReportResponse(
                metrics=metrics,
                recommendation="本周疼痛或疲劳偏高，建议生成一个降低强度的训练计划草案，等待你确认。",
                adjustment_proposal=proposal,
            )

    return WeeklyReportResponse(
        metrics=metrics,
        recommendation="本周反馈整体稳定，暂时保持当前训练计划。",
        adjustment_proposal=None,
    )


def _build_weekly_metrics(
    sessions: list[WorkoutSessionResponse],
) -> WeeklyReportMetrics:
    session_count = len(sessions)
    completed_sessions = sum(1 for session in sessions if session.completed)
    all_rpes = [workout_set.rpe for session in sessions for workout_set in session.sets]

    return WeeklyReportMetrics(
        session_count=session_count,
        completed_sessions=completed_sessions,
        completion_rate=_round_ratio(completed_sessions, session_count),
        average_rpe=_average(all_rpes),
        average_fatigue=_average([session.fatigue_level for session in sessions]),
        max_pain=max((session.pain_level for session in sessions), default=None),
    )


def _needs_lower_intensity(metrics: WeeklyReportMetrics) -> bool:
    return (metrics.max_pain is not None and metrics.max_pain >= 7) or (
        metrics.average_fatigue is not None and metrics.average_fatigue >= 8
    )


def _get_latest_plan(user_id: str):
    plans = training_plan_repository.list_by_user(user_id)
    if not plans:
        return None

    return plans[0]


def _lower_plan_intensity(plan: TrainingPlanDraft) -> TrainingPlanDraft:
    adjusted_plan = plan.model_copy(deep=True)
    for day in adjusted_plan.days:
        for exercise in day.exercises:
            exercise.target_rpe = max(5, exercise.target_rpe - 1)

    return adjusted_plan


def _average(values: list[float | int]) -> float | None:
    if not values:
        return None

    return round(sum(values) / len(values), 2)


def _round_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0

    return round(numerator / denominator, 2)
