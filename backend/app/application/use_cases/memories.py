from dataclasses import dataclass

from app.application.errors import NotFoundError
from app.domain.models import (
    UserMemoryCreate,
    UserMemoryListResponse,
    UserMemoryResponse,
)
from app.ports.repositories import UserMemoryRepositoryPort


@dataclass(frozen=True)
class MemoryUseCases:
    """用户长期记忆应用用例。"""

    repository: UserMemoryRepositoryPort

    def create(
        self,
        user_id: str,
        memory: UserMemoryCreate,
    ) -> UserMemoryResponse:
        """
        创建用户长期记忆。

        :param user_id: 用户标识。
        :param memory: 待保存的记忆。
        :return: 已保存的记忆。
        """
        return self.repository.create(user_id=user_id, memory=memory)

    def list(self, user_id: str) -> UserMemoryListResponse:
        """
        查询用户长期记忆。

        :param user_id: 用户标识。
        :return: 用户长期记忆列表响应。
        """
        return UserMemoryListResponse(
            memories=self.repository.list_by_user(user_id)
        )

    def delete(self, user_id: str, memory_id: int) -> None:
        """
        删除属于当前用户的长期记忆。

        :param user_id: 用户标识。
        :param memory_id: 记忆标识。
        :return: 无返回值。
        """
        deleted = self.repository.delete_by_id_for_user(
            user_id=user_id,
            memory_id=memory_id,
        )
        if not deleted:
            raise NotFoundError("Memory not found.")
