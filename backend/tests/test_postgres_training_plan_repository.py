import asyncio
from datetime import date

from sqlalchemy import delete

from app.core.config import AppSettings
from app.domain.models import (
    ExercisePrescription,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanStatus,
    WorkoutDayDraft,
)
from app.infrastructure.persistence.postgres.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgres.models import (
    TrainingPlanProposalRecord,
    TrainingPlanRecord,
)
from app.infrastructure.persistence.postgres.training_plan_repository import (
    TrainingPlanRepository,
)


DATABASE_URL = AppSettings.from_env().test_database_url


async def _assert_formal_plan_can_be_saved() -> None:
    """
    验证正式训练计划可以关联 Proposal 并保存到 PostgreSQL。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    user_id = "training-plan-save-user"

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

    try:
        async with session_factory() as write_session:
            proposal = TrainingPlanProposalRecord(
                user_id=user_id,
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

            repository = TrainingPlanRepository(write_session)
            saved_plan = await repository.save(
                user_id,
                plan,
                safety_check,
                source_proposal_id=proposal.id,
                version=1,
            )
            await write_session.commit()

        assert saved_plan.version == 1
        assert saved_plan.status == TrainingPlanStatus.SCHEDULED
        assert saved_plan.source_proposal_id == proposal.id
        assert saved_plan.plan == plan
        assert saved_plan.safety_check == safety_check

        async with session_factory() as read_session:
            repository = TrainingPlanRepository(read_session)


            record = await read_session.get(
                TrainingPlanRecord,
                saved_plan.id,
            )
            user_plans = await repository.list_by_user(user_id)
            unrelated_plans = await repository.list_by_user(
                "another-user"
            )

            found_plan = await repository.get_by_id_for_user(
                user_id,
                saved_plan.id,
            )
            another_user_plan = await repository.get_by_id_for_user(
                "another-user",
                saved_plan.id,
            )
            missing_plan = await repository.get_by_id_for_user(
                user_id,
                saved_plan.id + 9999,
            )



        replacement_plan = plan.model_copy(
            update={
                "goal_summary": "替换后的正式训练计划。",
            }
        )

        async with session_factory() as replacement_session:
            repository = TrainingPlanRepository(
                replacement_session
            )

            another_user_update = await repository.mark_superseded(
                "another-user",
                saved_plan.id,
            )
            superseded_plan = await repository.mark_superseded(
                user_id,
                saved_plan.id,
            )
            repeated_update = await repository.mark_superseded(
                user_id,
                saved_plan.id,
            )

            replacement_proposal = TrainingPlanProposalRecord(
                user_id=user_id,
                proposal_type="training_plan",
                operation="replace",
                target_week_start=replacement_plan.week_start,
                revision=1,
                status="approved",
                plan_snapshot=replacement_plan.model_dump(mode="json"),
                safety_check=safety_check.model_dump(mode="json"),
                generation_summary=replacement_plan.goal_summary,
            )
            replacement_session.add(replacement_proposal)
            await replacement_session.flush()

            saved_replacement = await repository.save(
                user_id,
                replacement_plan,
                safety_check,
                source_proposal_id=replacement_proposal.id,
                version=2,
            )
            await replacement_session.commit()



        assert record is not None
        assert record.user_id == user_id
        assert record.source_proposal_id == proposal.id
        assert record.plan_data == plan.model_dump(mode="json")
        assert [item.id for item in user_plans] == [saved_plan.id]
        assert unrelated_plans == []
        assert found_plan == saved_plan
        assert another_user_plan is None
        assert missing_plan is None


        assert another_user_update is None
        assert superseded_plan is not None
        assert superseded_plan.status == TrainingPlanStatus.SUPERSEDED
        assert repeated_update is None

        assert saved_replacement.version == 2
        assert saved_replacement.status == TrainingPlanStatus.SCHEDULED
        assert saved_replacement.plan == replacement_plan


        async with session_factory() as history_session:
            repository = TrainingPlanRepository(history_session)
            updated_history = await repository.list_by_user(user_id)

        assert [item.id for item in updated_history] == [
            saved_replacement.id,
            saved_plan.id,
        ]
        assert updated_history[0].status == TrainingPlanStatus.SCHEDULED
        assert updated_history[1].status == TrainingPlanStatus.SUPERSEDED
    finally:
        async with session_factory() as cleanup_session:
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

        await engine.dispose()


def test_formal_plan_can_be_saved_and_listed_for_its_user() -> None:
    """
    验证正式训练计划的保存、列表查询、单项查询和用户隔离。

    :return: 无返回值。
    """
    asyncio.run(_assert_formal_plan_can_be_saved())