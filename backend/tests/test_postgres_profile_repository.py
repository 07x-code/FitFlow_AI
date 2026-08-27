import asyncio

from app.core.config import AppSettings
from app.domain.models.profile import FitnessGoal, FitnessProfileCreate, Sex
from app.infrastructure.persistence.postgres.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgres.profile_repository import (
    ProfileRepository,
)
from app.infrastructure.persistence.postgres.models import FitnessProfileRecord

from sqlalchemy import delete

DATABASE_URL = AppSettings.from_env().test_database_url


async def _assert_profile_can_be_saved_and_loaded() -> None:
    """
    验证 PostgreSQL Repository 可以保存并读取用户画像。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)

    profile = FitnessProfileCreate(
        age=28,
        sex=Sex.MALE,
        height_cm=178,
        weight_kg=72.5,
        goal=FitnessGoal.MUSCLE_GAIN,
        sessions_per_week=3,
        session_minutes=60,
        health_flags=["knee_discomfort"],
    )

    user_id = "profile-user-1"

    try:
        async with session_factory() as write_session:
            repository = ProfileRepository(write_session)
            await repository.save(user_id, profile)
            await write_session.commit()

        async with session_factory() as read_session:
            repository = ProfileRepository(read_session)
            saved_profile = await repository.get(user_id)

            assert saved_profile == profile
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.execute(
                delete(FitnessProfileRecord).where(
                    FitnessProfileRecord.user_id == user_id
                )
            )
            await cleanup_session.commit()

        await engine.dispose()


def test_profile_repository_saves_and_gets_profile() -> None:
    """
    验证 PostgreSQL 用户画像仓储的保存和查询行为。

    :return: 无返回值。
    """
    asyncio.run(_assert_profile_can_be_saved_and_loaded())



async def _assert_profiles_are_isolated_by_user() -> None:
    """
    验证用户只能读取属于自己的健身画像。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)

    profile = FitnessProfileCreate(
        age=30,
        sex=Sex.FEMALE,
        height_cm=165,
        weight_kg=58,
        goal=FitnessGoal.GENERAL_FITNESS,
        sessions_per_week=3,
        session_minutes=45,
        health_flags=[],
    )

    try:
        async with session_factory() as session:
            repository = ProfileRepository(session)

            await repository.save("profile-owner", profile)

            assert await repository.get("profile-owner") == profile
            assert await repository.get("another-user") is None

            await session.rollback()
    finally:
        await engine.dispose()


def test_profile_repository_isolates_profiles_by_user() -> None:
    """
    验证 PostgreSQL 用户画像仓储按用户标识隔离数据。

    :return: 无返回值。
    """
    asyncio.run(_assert_profiles_are_isolated_by_user())



async def _assert_existing_profile_can_be_updated() -> None:
    """
    验证重复保存同一用户画像时会更新原记录。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)

    original_profile = FitnessProfileCreate(
        age=26,
        sex=Sex.MALE,
        height_cm=175,
        weight_kg=70,
        goal=FitnessGoal.GENERAL_FITNESS,
        sessions_per_week=2,
        session_minutes=40,
        health_flags=[],
    )
    updated_profile = FitnessProfileCreate(
        age=27,
        sex=Sex.MALE,
        height_cm=175,
        weight_kg=72,
        goal=FitnessGoal.MUSCLE_GAIN,
        sessions_per_week=4,
        session_minutes=60,
        health_flags=["shoulder_discomfort"],
    )

    try:
        async with session_factory() as session:
            repository = ProfileRepository(session)

            await repository.save("profile-update-user", original_profile)
            await repository.save("profile-update-user", updated_profile)

            assert await repository.get("profile-update-user") == updated_profile

            await session.rollback()
    finally:
        await engine.dispose()


def test_profile_repository_updates_existing_profile() -> None:
    """
    验证 PostgreSQL 用户画像仓储可以更新已有画像。

    :return: 无返回值。
    """
    asyncio.run(_assert_existing_profile_can_be_updated())