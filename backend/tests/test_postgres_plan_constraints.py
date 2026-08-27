import asyncio
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import AppSettings
from app.infrastructure.persistence.postgres.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgres.models import (
    TrainingPlanProposalRecord,
    TrainingPlanRecord,
)


DATABASE_URL = AppSettings.from_env().test_database_url


async def _assert_current_plan_is_unique_per_user_and_week() -> None:
    """
    验证同一用户同一自然周只能存在一个当前正式计划。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    user_id = "current-plan-unique-user"
    week_start = date(2026, 8, 24)
    week_end = date(2026, 8, 30)

    try:
        async with session_factory() as session:
            first_proposal = TrainingPlanProposalRecord(
                user_id=user_id,
                operation="create",
                target_week_start=week_start,
                revision=1,
                status="approved",
                plan_snapshot={"days": []},
                safety_check={"valid": True, "violations": []},
                generation_summary="第一版计划。",
            )
            second_proposal = TrainingPlanProposalRecord(
                user_id=user_id,
                operation="replace",
                target_week_start=week_start,
                revision=1,
                status="approved",
                plan_snapshot={"days": []},
                safety_check={"valid": True, "violations": []},
                generation_summary="第二版计划。",
            )
            session.add_all([first_proposal, second_proposal])
            await session.flush()

            first_plan = TrainingPlanRecord(
                user_id=user_id,
                week_start=week_start,
                week_end=week_end,
                timezone="Asia/Shanghai",
                version=1,
                status="scheduled",
                source_proposal_id=first_proposal.id,
                plan_data={"days": []},
                safety_check={"valid": True, "violations": []},
            )
            session.add(first_plan)
            await session.flush()

            second_plan = TrainingPlanRecord(
                user_id=user_id,
                week_start=week_start,
                week_end=week_end,
                timezone="Asia/Shanghai",
                version=2,
                status="active",
                source_proposal_id=second_proposal.id,
                plan_data={"days": []},
                safety_check={"valid": True, "violations": []},
            )
            session.add(second_plan)

            with pytest.raises(IntegrityError):
                await session.flush()

            await session.rollback()
    finally:
        await engine.dispose()


def test_current_plan_is_unique_per_user_and_week() -> None:
    """
    验证 PostgreSQL 拒绝同一用户同一周的重复当前计划。

    :return: 无返回值。
    """
    asyncio.run(_assert_current_plan_is_unique_per_user_and_week())