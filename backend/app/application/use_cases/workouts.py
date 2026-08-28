from dataclasses import dataclass

from app.application.errors import InvalidRequestError, NotFoundError
from app.domain.models import (
    WorkoutDayDraft,
    WorkoutHistoryResponse,
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
)
from app.ports.repositories import (
    TrainingPlanRepositoryPort,
    WorkoutSessionRepositoryPort,
)


@dataclass(frozen=True)
class WorkoutUseCases:
    """训练记录应用用例。"""

    plans: TrainingPlanRepositoryPort
    sessions: WorkoutSessionRepositoryPort

    async def create_session(
        self,
        user_id: str,
        plan_id: int,
        session: WorkoutSessionCreate,
    ) -> WorkoutSessionResponse:
        """
        校验并保存一次训练记录。

        :param user_id: 用户标识。
        :param plan_id: 正式训练计划标识。
        :param session: 待保存的训练记录。
        :return: 已保存的训练记录。
        """
        plan = await self.plans.get_by_id_for_user(user_id, plan_id)
        if plan is None:
            raise NotFoundError("Training plan not found.")

        plan_day = self._get_plan_day(plan.plan.days, session.plan_day_index)
        self._validate_logged_exercises(session, plan_day)
        return await self.sessions.save(
            user_id=user_id,
            plan_id=plan_id,
            plan_day_name=plan_day.name,
            session=session,
            safety_alert=self._build_safety_alert(session),
        )

    async def list_history(
        self,
        user_id: str,
        plan_id: int | None = None,
    ) -> WorkoutHistoryResponse:
        """
        查询用户训练记录。

        :param user_id: 用户标识。
        :param plan_id: 可选的训练计划筛选条件。
        :return: 用户训练历史响应。
        """
        sessions = await self.sessions.list_by_user(
            user_id,
            plan_id=plan_id,
        )
        return WorkoutHistoryResponse(
            sessions=sessions
        )

    @staticmethod
    def _get_plan_day(
        plan_days: list[WorkoutDayDraft],
        plan_day_index: int,
    ) -> WorkoutDayDraft:
        if plan_day_index > len(plan_days):
            raise InvalidRequestError(
                f"Plan day {plan_day_index} does not exist. "
                f"This plan has {len(plan_days)} days."
            )
        return plan_days[plan_day_index - 1]

    @staticmethod
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
            raise InvalidRequestError(
                {
                    "message": (
                        "Workout contains exercises outside the selected plan day."
                    ),
                    "unplanned_exercises": unplanned_names,
                }
            )

    @staticmethod
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
