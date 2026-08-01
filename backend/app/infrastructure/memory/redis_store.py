import json
from typing import Any, Protocol
from urllib.parse import quote

from app.domain.memory import WorkingMemoryItem


APPEND_AND_TRIM_SCRIPT = """
redis.call("ZADD", KEYS[1], ARGV[1], ARGV[2])
local capacity = tonumber(ARGV[4])
local count = redis.call("ZCARD", KEYS[1])

if count > capacity then
    local members = redis.call("ZRANGE", KEYS[1], 0, -1)
    table.sort(members, function(left, right)
        local left_item = cjson.decode(left)
        local right_item = cjson.decode(right)
        if left_item.importance == right_item.importance then
            if left_item.created_at == right_item.created_at then
                return left_item.id < right_item.id
            end
            return left_item.created_at < right_item.created_at
        end
        return left_item.importance < right_item.importance
    end)

    for index = 1, count - capacity do
        redis.call("ZREM", KEYS[1], members[index])
    end
end

redis.call("EXPIRE", KEYS[1], ARGV[3])
return 1
"""


class RedisClientPort(Protocol):
    """Redis 工作记忆适配器使用的最小客户端契约。"""

    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: object,
    ) -> object:
        """
        执行 Redis Lua 脚本。

        :param script: 待执行的 Lua 脚本。
        :param numkeys: 参数中键的数量。
        :param keys_and_args: Redis 键和脚本参数。
        :return: Lua 脚本执行结果。
        """

    def zrange(self, name: str, start: int, end: int) -> list[str | bytes]:
        """
        按分数顺序读取有序集合成员。

        :param name: Redis 键。
        :param start: 起始索引。
        :param end: 结束索引。
        :return: 有序集合成员。
        """

    def delete(self, *names: str) -> int:
        """
        删除一个或多个 Redis 键。

        :param names: 待删除的 Redis 键。
        :return: 实际删除的键数量。
        """


class RedisWorkingMemoryStore:
    """基于 Redis 有序集合的工作记忆存储。"""

    def __init__(
        self,
        client: RedisClientPort,
        *,
        ttl_seconds: int = 7200,
        capacity: int = 40,
        key_prefix: str = "fitflow:memory:working",
    ) -> None:
        """
        初始化 Redis 工作记忆存储。

        :param client: Redis 客户端。
        :param ttl_seconds: 会话没有新写入后保留的秒数。
        :param capacity: 每个会话允许保留的最大条目数。
        :param key_prefix: Redis 工作记忆键前缀。
        :return: 无返回值。
        """
        if ttl_seconds < 1:
            raise ValueError("working memory TTL must be at least 1 second")
        if capacity < 1:
            raise ValueError("working memory capacity must be at least 1")
        if not key_prefix.strip():
            raise ValueError("working memory key prefix must not be empty")

        self.client = client
        self.ttl_seconds = ttl_seconds
        self.capacity = capacity
        self.key_prefix = key_prefix.rstrip(":")

    @classmethod
    def from_url(
        cls,
        redis_url: str,
        *,
        ttl_seconds: int = 7200,
        capacity: int = 40,
    ) -> "RedisWorkingMemoryStore":
        """
        根据 Redis URL 创建工作记忆存储。

        :param redis_url: Redis 连接地址。
        :param ttl_seconds: 会话没有新写入后保留的秒数。
        :param capacity: 每个会话允许保留的最大条目数。
        :return: 已创建的 Redis 工作记忆存储。
        """
        try:
            from redis import Redis
        except ImportError as exc:
            raise RuntimeError(
                "Redis working memory requires the 'redis' package."
            ) from exc

        client = Redis.from_url(redis_url, decode_responses=True)
        return cls(
            client,
            ttl_seconds=ttl_seconds,
            capacity=capacity,
        )

    def append(
        self,
        user_id: str,
        session_id: str,
        item: WorkingMemoryItem,
    ) -> None:
        """
        原子追加工作记忆、执行容量淘汰并刷新 TTL。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param item: 待保存的工作记忆条目。
        :return: 无返回值。
        """
        key = self.build_key(user_id, session_id)
        payload = item.model_dump_json()
        self.client.eval(
            APPEND_AND_TRIM_SCRIPT,
            1,
            key,
            item.created_at.timestamp(),
            payload,
            self.ttl_seconds,
            self.capacity,
        )

    def list(
        self,
        user_id: str,
        session_id: str,
        *,
        limit: int | None = None,
    ) -> list[WorkingMemoryItem]:
        """
        按创建时间读取 Redis 中尚未过期的工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param limit: 最多返回的最近条目数，默认返回全部。
        :return: 指定会话内按时间升序排列的工作记忆。
        """
        if limit is not None and limit < 1:
            raise ValueError("working memory limit must be at least 1")

        start = -limit if limit is not None else 0
        members = self.client.zrange(
            self.build_key(user_id, session_id),
            start,
            -1,
        )
        return [
            WorkingMemoryItem.model_validate_json(_decode(member))
            for member in members
        ]

    def clear(self, user_id: str, session_id: str) -> None:
        """
        删除指定用户会话的 Redis 工作记忆键。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :return: 无返回值。
        """
        self.client.delete(self.build_key(user_id, session_id))

    def build_key(self, user_id: str, session_id: str) -> str:
        """
        生成经过转义的用户级会话 Redis 键。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :return: 格式为前缀、用户和会话组成的 Redis 键。
        """
        normalized_user_id = user_id.strip()
        normalized_session_id = session_id.strip()
        if not normalized_user_id:
            raise ValueError("user_id must not be empty")
        if not normalized_session_id:
            raise ValueError("session_id must not be empty")
        return (
            f"{self.key_prefix}:"
            f"{quote(normalized_user_id, safe='')}:"
            f"{quote(normalized_session_id, safe='')}"
        )


def _decode(value: str | bytes) -> str:
    """
    将 Redis 返回的成员统一转换为字符串。

    :param value: Redis 返回的字符串或字节数据。
    :return: UTF-8 字符串。
    """
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
