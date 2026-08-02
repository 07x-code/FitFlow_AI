from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from time import monotonic

from app.domain.models import WorkingMemoryItem
from app.domain.policies import trim_working_memory


@dataclass
class _SessionMemory:
    """进程内单个会话的工作记忆状态。"""

    items: list[WorkingMemoryItem]
    expires_at: float


class InMemoryWorkingMemoryStore:
    """支持 TTL、容量限制和用户隔离的进程内工作记忆。"""

    def __init__(
        self,
        *,
        ttl_seconds: int = 7200,
        capacity: int = 40,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        """
        初始化进程内工作记忆存储。

        :param ttl_seconds: 会话没有新写入后保留的秒数。
        :param capacity: 每个会话允许保留的最大条目数。
        :param clock: 用于计算 TTL 的单调时钟，测试时可注入。
        :return: 无返回值。
        """
        if ttl_seconds < 1:
            raise ValueError("working memory TTL must be at least 1 second")
        if capacity < 1:
            raise ValueError("working memory capacity must be at least 1")

        self.ttl_seconds = ttl_seconds
        self.capacity = capacity
        self._clock = clock
        self._sessions: dict[tuple[str, str], _SessionMemory] = {}
        self._lock = RLock()

    def append(
        self,
        user_id: str,
        session_id: str,
        item: WorkingMemoryItem,
    ) -> None:
        """
        追加工作记忆并刷新当前会话的 TTL。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param item: 待保存的工作记忆条目。
        :return: 无返回值。
        """
        key = _session_key(user_id, session_id)
        with self._lock:
            now = self._clock()
            session = self._sessions.get(key)
            items = (
                list(session.items)
                if session is not None and session.expires_at > now
                else []
            )
            items.append(item)
            self._sessions[key] = _SessionMemory(
                items=trim_working_memory(items, self.capacity),
                expires_at=now + self.ttl_seconds,
            )

    def list(
        self,
        user_id: str,
        session_id: str,
        *,
        limit: int | None = None,
    ) -> list[WorkingMemoryItem]:
        """
        读取尚未过期的工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param limit: 最多返回的最近条目数，默认返回全部。
        :return: 指定会话内按时间升序排列的工作记忆。
        """
        if limit is not None and limit < 1:
            raise ValueError("working memory limit must be at least 1")

        key = _session_key(user_id, session_id)
        with self._lock:
            session = self._sessions.get(key)
            if session is None:
                return []
            if session.expires_at <= self._clock():
                del self._sessions[key]
                return []

            items = list(session.items)
            return items[-limit:] if limit is not None else items

    def clear(self, user_id: str, session_id: str) -> None:
        """
        清理指定用户会话的工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :return: 无返回值。
        """
        key = _session_key(user_id, session_id)
        with self._lock:
            self._sessions.pop(key, None)


def _session_key(user_id: str, session_id: str) -> tuple[str, str]:
    """
    校验用户和会话标识并生成进程内隔离键。

    :param user_id: 用户标识。
    :param session_id: 会话标识。
    :return: 用户标识和会话标识组成的隔离键。
    """
    normalized_user_id = user_id.strip()
    normalized_session_id = session_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id must not be empty")
    if not normalized_session_id:
        raise ValueError("session_id must not be empty")
    return normalized_user_id, normalized_session_id
