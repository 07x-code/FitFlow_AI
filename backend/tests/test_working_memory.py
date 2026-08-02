import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.application.use_cases.working_memory import WorkingMemoryUseCases
from app.domain.models import (
    ConversationRole,
    WorkingMemoryItem,
    WorkingMemoryKind,
)
from app.infrastructure.memory.in_memory import InMemoryWorkingMemoryStore
from app.infrastructure.memory.redis_store import RedisWorkingMemoryStore


class AdjustableClock:
    """可由测试推进的单调时钟。"""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        """
        返回当前测试时间。

        :return: 当前测试时间。
        """
        return self.now

    def advance(self, seconds: float) -> None:
        """
        推进测试时间。

        :param seconds: 需要推进的秒数。
        :return: 无返回值。
        """
        self.now += seconds


class FakeRedisClient:
    """用于验证 Redis 适配器协议的轻量测试替身。"""

    def __init__(self) -> None:
        self.values: dict[str, list[tuple[float, str]]] = {}
        self.ttls: dict[str, int] = {}

    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: object,
    ) -> int:
        """
        模拟工作记忆 Lua 脚本的追加、淘汰和 TTL 行为。

        :param script: 待执行脚本。
        :param numkeys: Redis 键数量。
        :param keys_and_args: Redis 键和脚本参数。
        :return: 固定返回 1。
        """
        assert script
        assert numkeys == 1
        key = str(keys_and_args[0])
        score = float(keys_and_args[1])
        payload = str(keys_and_args[2])
        ttl = int(keys_and_args[3])
        capacity = int(keys_and_args[4])

        values = self.values.setdefault(key, [])
        values.append((score, payload))
        if len(values) > capacity:
            ranked = sorted(
                values,
                key=lambda pair: (
                    json.loads(pair[1])["importance"],
                    json.loads(pair[1])["created_at"],
                    json.loads(pair[1])["id"],
                ),
            )
            removed = {payload for _, payload in ranked[: len(values) - capacity]}
            self.values[key] = [
                pair for pair in values if pair[1] not in removed
            ]
        self.ttls[key] = ttl
        return 1

    def zrange(self, name: str, start: int, end: int) -> list[str]:
        """
        模拟按时间分数读取有序集合。

        :param name: Redis 键。
        :param start: 起始索引。
        :param end: 结束索引。
        :return: 选定范围内的 JSON 成员。
        """
        values = [
            payload
            for _, payload in sorted(self.values.get(name, []))
        ]
        normalized_start = len(values) + start if start < 0 else start
        normalized_start = max(normalized_start, 0)
        normalized_end = len(values) - 1 if end == -1 else end
        return values[normalized_start : normalized_end + 1]

    def delete(self, *names: str) -> int:
        """
        模拟删除 Redis 键。

        :param names: 待删除的 Redis 键。
        :return: 实际删除的键数量。
        """
        deleted = 0
        for name in names:
            if name in self.values:
                deleted += 1
                del self.values[name]
            self.ttls.pop(name, None)
        return deleted


def message(
    content: str,
    *,
    importance: float = 0.5,
    seconds: int = 0,
) -> WorkingMemoryItem:
    """
    创建用于测试的用户消息工作记忆。

    :param content: 消息内容。
    :param importance: 消息重要性。
    :param seconds: 相对测试基准时间的秒数。
    :return: 工作记忆条目。
    """
    return WorkingMemoryItem(
        id=content,
        kind=WorkingMemoryKind.MESSAGE,
        role=ConversationRole.USER,
        content=content,
        importance=importance,
        created_at=datetime(2026, 7, 31, tzinfo=timezone.utc)
        + timedelta(seconds=seconds),
    )


def test_working_memory_requires_type_specific_fields():
    with pytest.raises(ValidationError):
        WorkingMemoryItem(
            kind=WorkingMemoryKind.MESSAGE,
            content="缺少角色",
        )

    with pytest.raises(ValidationError):
        WorkingMemoryItem(
            kind=WorkingMemoryKind.TOOL_OBSERVATION,
            content="缺少工具名",
        )


def test_in_memory_store_isolates_users_and_sessions():
    store = InMemoryWorkingMemoryStore()
    store.append("user-a", "session-1", message("a-1"))
    store.append("user-a", "session-2", message("a-2"))
    store.append("user-b", "session-1", message("b-1"))

    assert [item.content for item in store.list("user-a", "session-1")] == [
        "a-1"
    ]
    assert [item.content for item in store.list("user-a", "session-2")] == [
        "a-2"
    ]
    assert [item.content for item in store.list("user-b", "session-1")] == [
        "b-1"
    ]


def test_in_memory_store_expires_and_clears_sessions():
    clock = AdjustableClock()
    store = InMemoryWorkingMemoryStore(ttl_seconds=10, clock=clock)
    use_cases = WorkingMemoryUseCases(store)
    store.append("user-a", "session-1", message("hello"))

    clock.advance(9)
    assert len(store.list("user-a", "session-1")) == 1
    clock.advance(1)
    assert store.list("user-a", "session-1") == []

    store.append("user-a", "session-1", message("new"))
    use_cases.end_session("user-a", "session-1")
    assert store.list("user-a", "session-1") == []


def test_capacity_evicts_low_importance_then_oldest():
    store = InMemoryWorkingMemoryStore(capacity=2)
    store.append("user", "session", message("old-low", importance=0.1))
    store.append(
        "user",
        "session",
        message("new-low", importance=0.1, seconds=1),
    )
    store.append(
        "user",
        "session",
        message("important", importance=1.0, seconds=2),
    )

    assert [item.content for item in store.list("user", "session")] == [
        "new-low",
        "important",
    ]


def test_redis_store_uses_isolated_key_ttl_capacity_and_clear():
    client = FakeRedisClient()
    store = RedisWorkingMemoryStore(
        client,
        ttl_seconds=120,
        capacity=2,
    )
    store.append("user/a", "session:1", message("low", importance=0.1))
    store.append(
        "user/a",
        "session:1",
        message("high", importance=1.0, seconds=1),
    )
    store.append(
        "user/a",
        "session:1",
        message("middle", importance=0.5, seconds=2),
    )

    key = "fitflow:memory:working:user%2Fa:session%3A1"
    assert client.ttls[key] == 120
    assert [item.content for item in store.list("user/a", "session:1")] == [
        "high",
        "middle",
    ]
    assert store.list("other-user", "session:1") == []

    store.clear("user/a", "session:1")
    assert store.list("user/a", "session:1") == []
