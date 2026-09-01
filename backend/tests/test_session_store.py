import asyncio

from app.core.config import AppSettings
from app.infrastructure.auth.session_store import (
    InMemorySessionStore,
    RedisSessionStore,
)
from app.ports.sessions import SessionStorePort


async def _assert_session_lifecycle(store: SessionStorePort) -> None:
    """
    验证登录会话的创建、读取和删除行为。

    :param store: 待验证的会话存储。
    :return: 无返回值。
    """
    await store.ping()
    token = await store.create("session-user")

    assert token != "session-user"
    assert await store.get_user_id(token) == "session-user"

    await store.delete(token)
    assert await store.get_user_id(token) is None
    await store.close()


def test_in_memory_session_store_supports_session_lifecycle() -> None:
    """
    验证进程内测试会话存储支持完整生命周期。

    :return: 无返回值。
    """
    store = InMemorySessionStore(ttl_seconds=60)
    asyncio.run(_assert_session_lifecycle(store))


def test_redis_session_store_supports_session_lifecycle() -> None:
    """
    验证 Redis 登录会话存储支持完整生命周期。

    :return: 无返回值。
    """
    settings = AppSettings.from_env()
    store = RedisSessionStore.from_url(
        settings.redis_url,
        ttl_seconds=60,
    )
    asyncio.run(_assert_session_lifecycle(store))
