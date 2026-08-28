import asyncio
from datetime import date, datetime, timedelta
import pytest
from uuid import uuid4

from sqlalchemy import delete

from app.core.config import AppSettings
from app.domain.models import (
    ExercisePrescription,
    SafetyCheckResult,
    TrainingPlanDraft,
    WorkoutDayDraft,
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSetLog,
)
from app.infrastructure.persistence.postgres.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgres.models import (
    TrainingPlanProposalRecord,
    TrainingPlanRecord,
    WorkoutSessionRecord,
)
from app.infrastructure.persistence.postgres.training_plan_repository import (
    TrainingPlanRepository,
)
from app.infrastructure.persistence.postgres.workout_session_repository import (
    WorkoutSessionRepository,
)


DATABASE_URL = AppSettings.from_env().test_database_url


async def _assert_workout_session_can_be_saved() -> None:
    """
    验证训练记录可以关联正式计划并保存到 PostgreSQL。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    user_id = f"workout-session-save-{uuid4().hex}"

    plan = TrainingPlanDraft(
        week_start=date(2026, 8, 24),
        week_end=date(2026, 8, 30),
        timezone="Asia/Shanghai",
        goal_summary="每周三次基础力量训练。",
        days=[
            WorkoutDayDraft(
                scheduled_date=date(2026, 8, 24),
                name="Day 1",
                focus="全身基础力量",
                estimated_minutes=60,
                exercises=[
                    ExercisePrescription(
                        exercise_name="Goblet Squat",
                        sets=3,
                        reps_min=8,
                        reps_max=12,
                        target_rpe=7,
                    )
                ],
            )
        ],
    )
    safety_check = SafetyCheckResult(
        valid=True,
        violations=[],
    )
    workout = WorkoutSessionCreate(
        plan_day_index=1,
        completed=True,
        fatigue_level=7,
        pain_level=2,
        notes="完成了第一天训练。",
        sets=[
            WorkoutSetLog(
                exercise_id="goblet-squat",
                exercise_name="Goblet Squat",
                set_number=1,
                weight_kg=12,
                reps=10,
                rpe=7,
            )
        ],
    )
    safety_alert = WorkoutSafetyAlert(
        level="info",
        message="继续保持当前训练强度。",
    )

    try:
        async with session_factory() as write_session:
            proposal = TrainingPlanProposalRecord(
                user_id=user_id,
                proposal_type="training_plan",
                operation="create",
                target_week_start=plan.week_start,
                revision=1,
                status="approved",
                plan_snapshot=plan.model_dump(mode="json"),
                safety_check=safety_check.model_dump(mode="json"),
                generation_summary=plan.goal_summary,
            )
            write_session.add(proposal)
            await write_session.flush()

            plan_repository = TrainingPlanRepository(write_session)
            saved_plan = await plan_repository.save(
                user_id,
                plan,
                safety_check,
                source_proposal_id=proposal.id,
                version=1,
            )

            workout_repository = WorkoutSessionRepository(
                write_session
            )
            saved_session = await workout_repository.save(
                user_id=user_id,
                plan_id=saved_plan.id,
                plan_day_name=plan.days[0].name,
                session=workout,
                safety_alert=safety_alert,
            )

            await write_session.commit()

        assert saved_session.plan_id == saved_plan.id
        assert saved_session.plan_day_index == 1
        assert saved_session.plan_day_name == plan.days[0].name
        assert saved_session.completed is True
        assert saved_session.fatigue_level == 7
        assert saved_session.pain_level == 2
        assert saved_session.notes == "完成了第一天训练。"
        assert saved_session.sets == workout.sets
        assert saved_session.safety_alert == safety_alert
        assert saved_session.created_at

        async with session_factory() as read_session:
            record = await read_session.get(
                WorkoutSessionRecord,
                saved_session.id,
            )


            repository = WorkoutSessionRepository(read_session)

            user_sessions = await repository.list_by_user(user_id)
            plan_sessions = await repository.list_by_user(
                user_id,
                plan_id=saved_plan.id,
            )
            another_plan_sessions = await repository.list_by_user(
                user_id,
                plan_id=saved_plan.id + 9999,
            )
            another_user_sessions = await repository.list_by_user(
                "another-user"
            )


            created_at = datetime.fromisoformat(
                saved_session.created_at
            )
            period_sessions = (
                await repository.list_by_user_in_period(
                    user_id,
                    created_at - timedelta(minutes=1),
                    created_at + timedelta(minutes=1),
                )
            )
            future_sessions = (
                await repository.list_by_user_in_period(
                    user_id,
                    created_at + timedelta(days=1),
                    created_at + timedelta(days=2),
                )
            )
            another_user_period_sessions = (
                await repository.list_by_user_in_period(
                    "another-user",
                    created_at - timedelta(minutes=1),
                    created_at + timedelta(minutes=1),
                )
            )

            with pytest.raises(
                ValueError,
                match="start_at 必须早于 end_at",
            ):
                await repository.list_by_user_in_period(
                    user_id,
                    created_at,
                    created_at,
                )

        assert record is not None
        assert record.user_id == user_id
        assert record.plan_id == saved_plan.id
        assert record.plan_day_index == workout.plan_day_index
        assert record.plan_day_name == plan.days[0].name
        assert record.completed is True
        assert record.fatigue_level == workout.fatigue_level
        assert record.pain_level == workout.pain_level
        assert record.notes == workout.notes
        assert record.sets_data == [
            workout_set.model_dump(mode="json")
            for workout_set in workout.sets
        ]
        assert record.safety_alert == safety_alert.model_dump(
            mode="json"
        )


        assert [item.id for item in user_sessions] == [
            saved_session.id
        ]
        assert [item.id for item in plan_sessions] == [
            saved_session.id
        ]
        assert another_plan_sessions == []
        assert another_user_sessions == []


        assert [item.id for item in period_sessions] == [
            saved_session.id
        ]
        assert future_sessions == []
        assert another_user_period_sessions == []
    finally:
        try:
            async with session_factory() as cleanup_session:
                await cleanup_session.execute(
                    delete(WorkoutSessionRecord).where(
                        WorkoutSessionRecord.user_id == user_id
                    )
                )
                await cleanup_session.execute(
                    delete(TrainingPlanRecord).where(
                        TrainingPlanRecord.user_id == user_id
                    )
                )
                await cleanup_session.execute(
                    delete(TrainingPlanProposalRecord).where(
                        TrainingPlanProposalRecord.user_id == user_id
                    )
                )
                await cleanup_session.commit()
        finally:
            await engine.dispose()


def test_workout_session_can_be_saved() -> None:
    """
    验证 PostgreSQL 仓储可以保存字段完整的训练记录。

    :return: 无返回值。
    """
    asyncio.run(_assert_workout_session_can_be_saved())