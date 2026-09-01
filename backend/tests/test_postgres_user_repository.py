import asyncio

from sqlalchemy import delete

from app.core.config import AppSettings
from app.core.passwords import hash_password
from app.domain.models import UserStatus
from app.infrastructure.persistence.postgres.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgres.models import UserRecord
from app.infrastructure.persistence.postgres.user_repository import UserRepository


DATABASE_URL = AppSettings.from_env().test_database_url


async def _assert_user_account_lifecycle() -> None:
    """
    验证用户账号的创建、查询、登录记录和禁用流程。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    email = "  Multi.User@Example.com  "
    normalized_email = "multi.user@example.com"

    try:
        async with session_factory() as session:
            await session.execute(
                delete(UserRecord).where(
                    UserRecord.email_normalized == normalized_email
                )
            )
            repository = UserRepository(session)
            password_hash = hash_password("FitFlow-password-2026")
            created = await repository.create(
                email,
                password_hash,
                "  测试用户  ",
            )

            assert created.email == "Multi.User@Example.com"
            assert created.display_name == "测试用户"
            assert created.status == UserStatus.ACTIVE
            assert not hasattr(created, "password_hash")
            assert await repository.get_by_id(created.id) == created
            assert await repository.get_by_email(
                "MULTI.USER@example.com"
            ) == created

            authentication = await repository.get_authentication_by_email(
                normalized_email
            )
            assert authentication == (created, password_hash)

            logged_in = await repository.mark_login(created.id)
            assert logged_in is not None
            assert logged_in.last_login_at is not None

            disabled = await repository.disable(created.id)
            assert disabled is not None
            assert disabled.status == UserStatus.DISABLED
            await session.rollback()
    finally:
        await engine.dispose()


def test_user_repository_supports_account_lifecycle() -> None:
    """
    验证 PostgreSQL 用户账号仓储支持认证所需生命周期。

    :return: 无返回值。
    """
    asyncio.run(_assert_user_account_lifecycle())
