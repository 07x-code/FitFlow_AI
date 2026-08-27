import asyncio

from sqlalchemy import delete

from app.core.config import AppSettings
from app.domain.models.user_memory import MemoryType, UserMemoryCreate
from app.infrastructure.persistence.postgres.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgres.models import UserMemoryRecord
from app.infrastructure.persistence.postgres.user_memory_repository import (
    UserMemoryRepository,
)


DATABASE_URL = AppSettings.from_env().test_database_url


async def _assert_memory_can_be_created_and_listed() -> None:
    """
    验证长期记忆提交后可以通过新 Session 查询。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    user_id = "memory-create-user"

    memory = UserMemoryCreate(
        type=MemoryType.PREFERRED_EQUIPMENT,
        content="更喜欢使用哑铃训练",
        source="user",
    )

    try:
        async with session_factory() as write_session:
            repository = UserMemoryRepository(write_session)
            created_memory = await repository.create(user_id, memory)
            await write_session.commit()

        assert created_memory.id > 0
        assert created_memory.type == memory.type
        assert created_memory.content == memory.content
        assert created_memory.source == memory.source
        assert created_memory.created_at

        async with session_factory() as read_session:
            repository = UserMemoryRepository(read_session)
            memories = await repository.list_by_user(user_id)

        assert memories == [created_memory]
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.execute(
                delete(UserMemoryRecord).where(
                    UserMemoryRecord.user_id == user_id
                )
            )
            await cleanup_session.commit()

        await engine.dispose()


def test_user_memory_repository_creates_and_lists_memory() -> None:
    """
    验证 PostgreSQL 长期记忆仓储可以创建并查询记忆。

    :return: 无返回值。
    """
    asyncio.run(_assert_memory_can_be_created_and_listed())



async def _assert_memories_are_ordered_and_isolated() -> None:
    """
    验证长期记忆按用户隔离并按标识倒序返回。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    owner_id = "memory-list-owner"
    other_user_id = "memory-list-other"

    first_memory = UserMemoryCreate(
        type=MemoryType.TRAINING_TIME,
        content="工作日晚上训练",
        source="user",
    )
    second_memory = UserMemoryCreate(
        type=MemoryType.DISLIKED_EXERCISE,
        content="不喜欢波比跳",
        source="user",
    )
    other_memory = UserMemoryCreate(
        type=MemoryType.GENERAL_NOTE,
        content="其他用户的记忆",
        source="user",
    )

    try:
        async with session_factory() as write_session:
            repository = UserMemoryRepository(write_session)

            first_created = await repository.create(owner_id, first_memory)
            await repository.create(other_user_id, other_memory)
            second_created = await repository.create(owner_id, second_memory)

            await write_session.commit()

        async with session_factory() as read_session:
            repository = UserMemoryRepository(read_session)

            owner_memories = await repository.list_by_user(owner_id)
            other_memories = await repository.list_by_user(other_user_id)

        assert [memory.id for memory in owner_memories] == [
            second_created.id,
            first_created.id,
        ]
        assert [memory.content for memory in owner_memories] == [
            second_memory.content,
            first_memory.content,
        ]
        assert len(other_memories) == 1
        assert other_memories[0].content == other_memory.content
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.execute(
                delete(UserMemoryRecord).where(
                    UserMemoryRecord.user_id.in_(
                        [owner_id, other_user_id]
                    )
                )
            )
            await cleanup_session.commit()

        await engine.dispose()


def test_user_memory_repository_orders_and_isolates_memories() -> None:
    """
    验证 PostgreSQL 长期记忆仓储的排序和用户隔离。

    :return: 无返回值。
    """
    asyncio.run(_assert_memories_are_ordered_and_isolated())


async def _assert_memory_delete_respects_user_ownership() -> None:
    """
    验证只有记忆所属用户才能删除长期记忆。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    owner_id = "memory-delete-owner"
    other_user_id = "memory-delete-other"

    memory = UserMemoryCreate(
        type=MemoryType.PHYSICAL_LIMITATION,
        content="左膝不适",
        source="user",
    )

    try:
        async with session_factory() as create_session:
            repository = UserMemoryRepository(create_session)
            created_memory = await repository.create(owner_id, memory)
            await create_session.commit()

        async with session_factory() as wrong_user_session:
            repository = UserMemoryRepository(wrong_user_session)

            deleted = await repository.delete_by_id_for_user(
                other_user_id,
                created_memory.id,
            )

            assert deleted is False
            await wrong_user_session.commit()

        async with session_factory() as check_session:
            repository = UserMemoryRepository(check_session)
            assert await repository.list_by_user(owner_id) == [created_memory]

        async with session_factory() as owner_session:
            repository = UserMemoryRepository(owner_session)

            deleted = await repository.delete_by_id_for_user(
                owner_id,
                created_memory.id,
            )
            deleted_again = await repository.delete_by_id_for_user(
                owner_id,
                created_memory.id,
            )

            assert deleted is True
            assert deleted_again is False
            await owner_session.commit()

        async with session_factory() as final_session:
            repository = UserMemoryRepository(final_session)
            assert await repository.list_by_user(owner_id) == []
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.execute(
                delete(UserMemoryRecord).where(
                    UserMemoryRecord.user_id.in_(
                        [owner_id, other_user_id]
                    )
                )
            )
            await cleanup_session.commit()

        await engine.dispose()


def test_user_memory_delete_respects_user_ownership() -> None:
    """
    验证 PostgreSQL 长期记忆仓储的删除权限和返回值。

    :return: 无返回值。
    """
    asyncio.run(_assert_memory_delete_respects_user_ownership())