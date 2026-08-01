from typing import Protocol

from app.domain.memory import WorkingMemoryItem


class WorkingMemoryStorePort(Protocol):
    """会话级工作记忆存储端口。"""

    def append(
        self,
        user_id: str,
        session_id: str,
        item: WorkingMemoryItem,
    ) -> None:
        """
        向指定用户会话追加一条工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param item: 待保存的工作记忆条目。
        :return: 无返回值。
        """

    def list(
        self,
        user_id: str,
        session_id: str,
        *,
        limit: int | None = None,
    ) -> list[WorkingMemoryItem]:
        """
        按创建时间读取指定用户会话的工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param limit: 最多返回的最近条目数，默认返回当前全部条目。
        :return: 指定会话内按时间升序排列的工作记忆。
        """

    def clear(self, user_id: str, session_id: str) -> None:
        """
        清理指定用户会话的全部工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :return: 无返回值。
        """
