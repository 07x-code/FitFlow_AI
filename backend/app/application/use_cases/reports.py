from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.application.errors import ConflictError
from app.domain.models import (
    SafetyCheckResult,
    TrainingPlanDraft,
    WeeklyReportMetrics,
    WeeklyReportResponse,
    WorkoutSessionResponse,
)
from app.domain.training_rules import validate_beginner_plan
from app.ports.repositories import (
    TrainingPlanProposalRepositoryPort,
    TrainingPlanRepositoryPort,
    WorkoutSessionRepositoryPort,
)
REPORT_TIMEZONE = ZoneInfo("Asia/Shanghai")



@dataclass(frozen=True)
class ReportUseCases:
    """训练周报应用用例。"""

    plans: TrainingPlanRepositoryPort
    sessions: WorkoutSessionRepositoryPort
    proposals: TrainingPlanProposalRepositoryPort

    async def create_weekly(
        self,
        user_id: str,
    ) -> WeeklyReportResponse:
        """
        根据用户当前自然周的训练记录生成周报和可选调整 Proposal。

        :param user_id: 用户标识。
        :return: 训练周报。
        """
        start_at, end_at = _current_week_period()
        sessions = await self.sessions.list_by_user_in_period(
            user_id,
            start_at,
            end_at,
        )
        metrics = self._build_weekly_metrics(sessions)

        if not self._needs_lower_intensity(metrics):
            return WeeklyReportResponse(
                metrics=metrics,
                recommendation="本周反馈整体稳定，暂时保持当前训练计划。",
                adjustment_proposal=None,
            )

        base_plan = await self.plans.get_by_id_for_user(
            user_id,
            sessions[0].plan_id,
        )
        if base_plan is None:
            raise ConflictError("当前周训练记录关联的训练计划不存在。")

        adjusted_plan = self._lower_plan_intensity(base_plan.plan)
        safety_check = SafetyCheckResult.model_validate(
            validate_beginner_plan(adjusted_plan)
        )
        proposal = await self.proposals.create_replacement(
            user_id=user_id,
            base_plan_id=base_plan.id,
            plan=adjusted_plan,
            safety_check=safety_check,
        )
        if proposal is None:
            raise ConflictError("无法为当前训练计划创建调整 Proposal。")

        return WeeklyReportResponse(
            metrics=metrics,
            recommendation=(
                "本周疼痛或疲劳偏高，建议生成一个降低强度的训练计划草案，等待你确认。"
            ),
            adjustment_proposal=proposal,
        )

    @staticmethod
    def _build_weekly_metrics(
        sessions: list[WorkoutSessionResponse],
    ) -> WeeklyReportMetrics:
        session_count = len(sessions)
        completed_sessions = sum(
            1 for session in sessions if session.completed
        )
        all_rpes = [
            workout_set.rpe
            for session in sessions
            for workout_set in session.sets
        ]
        return WeeklyReportMetrics(
            session_count=session_count,
            completed_sessions=completed_sessions,
            completion_rate=_round_ratio(
                completed_sessions,
                session_count,
            ),
            average_rpe=_average(all_rpes),
            average_fatigue=_average(
                [session.fatigue_level for session in sessions]
            ),
            max_pain=max(
                (session.pain_level for session in sessions),
                default=None,
            ),
        )

    @staticmethod
    def _needs_lower_intensity(metrics: WeeklyReportMetrics) -> bool:
        return (
            metrics.max_pain is not None and metrics.max_pain >= 7
        ) or (
            metrics.average_fatigue is not None
            and metrics.average_fatigue >= 8
        )

    @staticmethod
    def _lower_plan_intensity(
        plan: TrainingPlanDraft,
    ) -> TrainingPlanDraft:
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


def _current_week_period() -> tuple[datetime, datetime]:
    """
    计算 Asia/Shanghai 时区下当前自然周的查询区间。

    :return: 本周一零点到下周一零点的左闭右开时间区间。
    """
    now = datetime.now(REPORT_TIMEZONE)
    monday = now.date() - timedelta(days=now.weekday())
    start_at = datetime.combine(
        monday,
        time.min,
        tzinfo=REPORT_TIMEZONE,
    )
    return start_at, start_at + timedelta(days=7)