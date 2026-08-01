from dataclasses import dataclass

from app.domain.memory import WorkingMemoryListResponse
from app.ports.working_memory import WorkingMemoryStorePort


@dataclass(frozen=True)
class WorkingMemoryUseCases:
    """工作记忆查询与会话生命周期用例。"""

    store: WorkingMemoryStorePort

    def list(
        self,
        user_id: str,
        session_id: str,
    ) -> WorkingMemoryListResponse:
        """
        读取指定用户会话的工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :return: 包含会话标识和工作记忆条目的响应。
        """
        return WorkingMemoryListResponse(
            session_id=session_id,
            items=self.store.list(user_id, session_id),
        )

    def end_session(self, user_id: str, session_id: str) -> None:
        """
        结束会话并立即清理对应工作记忆。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :return: 无返回值。
        """
        self.store.clear(user_id, session_id)
