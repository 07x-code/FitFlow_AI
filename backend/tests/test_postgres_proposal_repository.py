import asyncio
from datetime import date

from sqlalchemy import delete, update

from app.core.config import AppSettings
from app.domain.models import (
    ExercisePrescription,
    ProposalOperation,
    ProposalStatus,
    ProposalType,
    SafetyCheckResult,
    TrainingPlanDraft,
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
from app.infrastructure.persistence.postgres.proposal_repository import (
    TrainingPlanProposalRepository,
)
from app.infrastructure.persistence.postgres.training_plan_repository import (
    TrainingPlanRepository,
)

DATABASE_URL = AppSettings.from_env().test_database_url


async def _assert_pending_training_plan_proposal_can_be_created() -> None:
    """
    验证正式训练计划可以关联 Proposal 并保存到 PostgreSQL。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    user_id = "proposal-create-user"

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
        async with session_factory() as session:
            repository = TrainingPlanProposalRepository(session)

            proposal = await repository.create(
                user_id,
                plan,
                safety_check,
            )
            await session.commit()

        async with session_factory() as read_session:
            repository = TrainingPlanProposalRepository(read_session)

            user_proposals = await repository.list_by_user(user_id)
            another_user_proposals = await repository.list_by_user(
                "another-user"
            )

            found_proposal = await repository.get_by_id_for_user(
                user_id,
                proposal.id,
            )
            another_user_proposal = (
                await repository.get_by_id_for_user(
                    "another-user",
                    proposal.id,
                )
            )
            missing_proposal = await repository.get_by_id_for_user(
                user_id,
                proposal.id + 9999,
            )

        async with session_factory() as decision_session:
            repository = TrainingPlanProposalRepository(
                decision_session
            )

            approving_proposal = await repository.mark_approving(
                user_id,
                proposal.id,
            )
            repeated_transition = await repository.mark_approving(
                user_id,
                proposal.id,
            )
            another_user_transition = await repository.mark_approving(
                "another-user",
                proposal.id,
            )

            await decision_session.commit()


        async with session_factory() as approval_session:
            proposal_repository = TrainingPlanProposalRepository(
                approval_session
            )
            plan_repository = TrainingPlanRepository(approval_session)

            approved_plan = await plan_repository.save(
                user_id,
                plan,
                safety_check,
                source_proposal_id=proposal.id,
                version=1,
            )

            another_user_approval = await proposal_repository.approve(
                "another-user",
                proposal.id,
                approved_plan.id,
                "采用这份计划。",
            )
            approved_proposal = await proposal_repository.approve(
                user_id,
                proposal.id,
                approved_plan.id,
                "采用这份计划。",
            )
            repeated_approval = await proposal_repository.approve(
                user_id,
                proposal.id,
                approved_plan.id,
                "再次批准。",
            )

            await approval_session.commit()



        async with session_factory() as rejection_session:
            repository = TrainingPlanProposalRepository(
                rejection_session
            )

            rejected_candidate = await repository.create(
                user_id,
                plan,
                safety_check,
            )

            another_user_rejection = await repository.reject(
                "another-user",
                rejected_candidate.id,
                "训练时间不合适。",
            )
            rejected_proposal = await repository.reject(
                user_id,
                rejected_candidate.id,
                "训练时间不合适。",
            )
            repeated_rejection = await repository.reject(
                user_id,
                rejected_candidate.id,
                "再次拒绝。",
            )

            await rejection_session.commit()

        


        revised_plan = plan.model_copy(
            update={
                "goal_summary": "根据用户反馈调整训练安排。",
            }
        )

        async with session_factory() as revision_session:
            repository = TrainingPlanProposalRepository(
                revision_session
            )

            revision_source = await repository.create(
                user_id,
                plan,
                safety_check,
            )

            another_user_revision = await repository.create_revision(
                "another-user",
                revision_source.id,
                revised_plan,
                safety_check,
            )
            revised_proposal = await repository.create_revision(
                user_id,
                revision_source.id,
                revised_plan,
                safety_check,
            )
            repeated_revision = await repository.create_revision(
                user_id,
                revision_source.id,
                revised_plan,
                safety_check,
            )
            superseded_source = await repository.get_by_id_for_user(
                user_id,
                revision_source.id,
            )

            await revision_session.commit()



        replacement_plan = plan.model_copy(
            update={
                "goal_summary": "替换当前正式训练计划。",
            }
        )

        async with session_factory() as replacement_session:
            repository = TrainingPlanProposalRepository(
                replacement_session
            )

            closed_revision = await repository.reject(
                user_id,
                revised_proposal.id,
                "改为调整当前正式计划。",
            )

            another_user_replacement = (
                await repository.create_replacement(
                    "another-user",
                    approved_plan.id,
                    replacement_plan,
                    safety_check,
                )
            )
            missing_base_replacement = (
                await repository.create_replacement(
                    user_id,
                    approved_plan.id + 9999,
                    replacement_plan,
                    safety_check,
                )
            )
            replacement_proposal = (
                await repository.create_replacement(
                    user_id,
                    approved_plan.id,
                    replacement_plan,
                    safety_check,
                )
            )

            await replacement_session.commit()


        assert proposal.type == ProposalType.TRAINING_PLAN
        assert proposal.operation == ProposalOperation.CREATE
        assert proposal.target_week_start == plan.week_start
        assert proposal.revision == 1
        assert proposal.status == ProposalStatus.PENDING
        assert proposal.plan == plan
        assert proposal.safety_check == safety_check
        assert proposal.generation_summary == plan.goal_summary
        assert proposal.base_plan_id is None
        assert proposal.parent_proposal_id is None
        assert proposal.approved_plan_id is None
        assert proposal.decided_at is None

        assert [item.id for item in user_proposals] == [proposal.id]
        assert another_user_proposals == []

        assert found_proposal == proposal
        assert another_user_proposal is None
        assert missing_proposal is None

        assert approving_proposal is not None
        assert approving_proposal.status == ProposalStatus.APPROVING
        assert repeated_transition is None
        assert another_user_transition is None



        assert another_user_approval is None
        assert approved_proposal is not None
        assert approved_proposal.status == ProposalStatus.APPROVED
        assert approved_proposal.approved_plan_id == approved_plan.id
        assert approved_proposal.decision_note == "采用这份计划。"
        assert approved_proposal.decided_at is not None
        assert repeated_approval is None



        assert another_user_rejection is None
        assert rejected_proposal is not None
        assert rejected_proposal.status == ProposalStatus.REJECTED
        assert rejected_proposal.decision_note == "训练时间不合适。"
        assert rejected_proposal.decided_at is not None
        assert rejected_proposal.approved_plan_id is None
        assert repeated_rejection is None



        assert another_user_revision is None
        assert revised_proposal is not None
        assert revised_proposal.operation == ProposalOperation.ADJUST
        assert revised_proposal.parent_proposal_id == revision_source.id
        assert revised_proposal.base_plan_id is None
        assert revised_proposal.revision == 2
        assert revised_proposal.status == ProposalStatus.PENDING
        assert revised_proposal.plan == revised_plan
        assert repeated_revision is None

        assert superseded_source is not None
        assert superseded_source.status == ProposalStatus.SUPERSEDED
        assert superseded_source.decided_at is not None


        assert closed_revision is not None
        assert closed_revision.status == ProposalStatus.REJECTED
        assert another_user_replacement is None
        assert missing_base_replacement is None

        assert replacement_proposal is not None
        assert replacement_proposal.operation == ProposalOperation.REPLACE
        assert replacement_proposal.base_plan_id == approved_plan.id
        assert replacement_proposal.parent_proposal_id is None
        assert replacement_proposal.revision == 1
        assert replacement_proposal.status == ProposalStatus.PENDING
        assert replacement_proposal.plan == replacement_plan
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.execute(
                update(TrainingPlanProposalRecord)
                .where(
                    TrainingPlanProposalRecord.user_id == user_id
                )
                .values(
                    approved_plan_id=None,
                    base_plan_id=None,
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

        await engine.dispose()


def test_pending_proposal_can_be_created_and_listed_for_its_user() -> None:
    """
    验证 Proposal 的创建、用户隔离查询和批准状态抢占。

    :return: 无返回值。
    """
    asyncio.run(_assert_pending_training_plan_proposal_can_be_created())