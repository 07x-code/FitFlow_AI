import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol

from app.ports.sessions import SessionStorePort


class AsyncRedisClientPort(Protocol):
    """登录会话存储使用的最小 Redis 异步客户端契约。"""

    async def set(
        self,
        name: str,
        value: str,
        *,
        ex: int,
    ) -> object:
        """
        保存带过期时间的字符串。

        :param name: Redis 键。
        :param value: 待保存的值。
        :param ex: 过期秒数。
        :return: Redis 执行结果。
        """
        ...

    async def getex(self, name: str, *, ex: int) -> str | None:
        """
        读取字符串并刷新过期时间。

        :param name: Redis 键。
        :param ex: 新的过期秒数。
        :return: Redis 字符串；不存在时返回 None。
        """
        ...

    async def delete(self, *names: str) -> object:
        """
        删除 Redis 键。

        :param names: 待删除的 Redis 键。
        :return: Redis 执行结果。
        """
        ...

    async def ping(self) -> object:
        """
        检查 Redis 连接。

        :return: Redis 执行结果。
        """
        ...

    async def aclose(self) -> None:
        """
        关闭 Redis 客户端。

        :return: 无返回值。
        """
        ...


class RedisSessionStore:
    """使用 Redis 保存不透明登录会话。"""

    def __init__(
        self,
        client: AsyncRedisClientPort,
        *,
        ttl_seconds: int,
        key_prefix: str = "fitflow:auth:session",
    ) -> None:
        """
        创建 Redis 登录会话存储。

        :param client: Redis 异步客户端。
        :param ttl_seconds: 会话空闲过期秒数。
        :param key_prefix: Redis 会话键前缀。
        :return: 无返回值。
        """
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix.rstrip(":")

    @classmethod
    def from_url(
        cls,
        redis_url: str,
        *,
        ttl_seconds: int,
    ) -> "RedisSessionStore":
        """
        根据 Redis URL 创建登录会话存储。

        :param redis_url: Redis 连接地址。
        :param ttl_seconds: 会话空闲过期秒数。
        :return: 已创建的 Redis 登录会话存储。
        """
        from redis.asyncio import Redis

        client = Redis.from_url(redis_url, decode_responses=True)
        return cls(client, ttl_seconds=ttl_seconds)

    async def create(self, user_id: str) -> str:
        """
        为用户创建新的不透明会话令牌。

        :param user_id: 用户标识。
        :return: 仅交付给客户端 Cookie 的会话令牌。
        """
        token = secrets.token_urlsafe(32)
        await self._client.set(
            self._build_key(token),
            user_id,
            ex=self._ttl_seconds,
        )
        return token

    async def get_user_id(self, token: str) -> str | None:
        """
        解析有效会话并刷新空闲过期时间。

        :param token: 客户端提交的会话令牌。
        :return: 会话所属用户标识；会话无效时返回 None。
        """
        if not token:
            return None
        return await self._client.getex(
            self._build_key(token),
            ex=self._ttl_seconds,
        )

    async def delete(self, token: str) -> None:
        """
        删除指定登录会话。

        :param token: 客户端提交的会话令牌。
        :return: 无返回值。
        """
        if token:
            await self._client.delete(self._build_key(token))

    async def ping(self) -> None:
        """
        检查 Redis 会话存储是否可用。

        :return: 无返回值。
        """
        await self._client.ping()

    async def close(self) -> None:
        """
        关闭 Redis 客户端连接。

        :return: 无返回值。
        """
        await self._client.aclose()

    def _build_key(self, token: str) -> str:
        """
        使用令牌摘要生成 Redis 键。

        :param token: 客户端持有的不透明会话令牌。
        :return: 不包含原始令牌的 Redis 会话键。
        """
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"{self._key_prefix}:{digest}"


class InMemorySessionStore:
    """供自动化测试使用的进程内登录会话存储。"""

    def __init__(self, *, ttl_seconds: int) -> None:
        """
        创建进程内登录会话存储。

        :param ttl_seconds: 会话空闲过期秒数。
        :return: 无返回值。
        """
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, tuple[str, datetime]] = {}

    async def create(self, user_id: str) -> str:
        """
        为用户创建新的测试会话。

        :param user_id: 用户标识。
        :return: 新创建的会话令牌。
        """
        token = secrets.token_urlsafe(32)
        self._sessions[token] = (user_id, self._expires_at())
        return token

    async def get_user_id(self, token: str) -> str | None:
        """
        解析有效测试会话并刷新空闲过期时间。

        :param token: 客户端提交的会话令牌。
        :return: 会话所属用户标识；会话无效时返回 None。
        """
        session = self._sessions.get(token)
        if session is None:
            return None

        user_id, expires_at = session
        if expires_at <= datetime.now(timezone.utc):
            self._sessions.pop(token, None)
            return None

        self._sessions[token] = (user_id, self._expires_at())
        return user_id

    async def delete(self, token: str) -> None:
        """
        删除指定测试会话。

        :param token: 客户端提交的会话令牌。
        :return: 无返回值。
        """
        self._sessions.pop(token, None)

    async def ping(self) -> None:
        """
        确认进程内会话存储可用。

        :return: 无返回值。
        """

    async def close(self) -> None:
        """
        清空进程内会话数据。

        :return: 无返回值。
        """
        self._sessions.clear()

    def _expires_at(self) -> datetime:
        """
        计算新的会话过期时间。

        :return: 基于当前时间的会话过期时间。
        """
        return datetime.now(timezone.utc) + timedelta(
            seconds=self._ttl_seconds
        )


def create_session_store(
    backend: str,
    *,
    redis_url: str,
    ttl_seconds: int,
) -> SessionStorePort:
    """
    根据配置创建登录会话存储。

    :param backend: 会话存储类型。
    :param redis_url: Redis 连接地址。
    :param ttl_seconds: 会话空闲过期秒数。
    :return: 已配置的登录会话存储。
    """
    if backend == "memory":
        return InMemorySessionStore(ttl_seconds=ttl_seconds)
    if backend == "redis":
        return RedisSessionStore.from_url(
            redis_url,
            ttl_seconds=ttl_seconds,
        )
    raise ValueError("session backend must be 'memory' or 'redis'")
