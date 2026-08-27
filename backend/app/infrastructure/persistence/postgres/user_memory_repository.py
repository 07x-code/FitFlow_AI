from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user_memory import (
    MemoryType,
    UserMemoryCreate,
    UserMemoryResponse,
)
from app.infrastructure.persistence.postgres.models import UserMemoryRecord


class UserMemoryRepository:
    """PostgreSQL 用户长期记忆仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        """
        创建用户长期记忆仓储。

        :param session: 当前数据库操作使用的异步 Session。
        :return: 无返回值。
        """
        self._session = session

    async def create(
        self,
        user_id: str,
        memory: UserMemoryCreate,
    ) -> UserMemoryResponse:
        """
        创建一条用户长期记忆。

        :param user_id: 用户标识。
        :param memory: 待保存的长期记忆。
        :return: 已创建的长期记忆。
        """
        record = UserMemoryRecord(
            user_id=user_id,
            memory_type=memory.type.value,
            content=memory.content,
            source=memory.source,
        )
        self._session.add(record)

        await self._session.flush()
        await self._session.refresh(record)

        return self._to_response(record)

    async def list_by_user(
        self,
        user_id: str,
    ) -> list[UserMemoryResponse]:
        """
        查询指定用户的有效长期记忆。

        :param user_id: 用户标识。
        :return: 按标识倒序排列的有效长期记忆列表。
        """
        statement = (
            select(UserMemoryRecord)
            .where(
                UserMemoryRecord.user_id == user_id,
                UserMemoryRecord.status == "active",
            )
            .order_by(UserMemoryRecord.id.desc())
        )
        records = await self._session.scalars(statement)

        return [self._to_response(record) for record in records]


    async def delete_by_id_for_user(
            self,
            user_id: str,
            memory_id: int,
    ) -> bool:
        """
        删除属于指定用户的长期记忆。

        :param user_id: 用户标识。
        :param memory_id: 长期记忆标识。
        :return: 找到并删除时返回 True,否则返回 False。
        """
        statement = select(UserMemoryRecord).where(
            UserMemoryRecord.id == memory_id,
            UserMemoryRecord.user_id == user_id,
        )
        record = await self._session.scalar(statement)

        if record is None:
            return False

        await self._session.delete(record)
        await self._session.flush()
        return True
    

    @staticmethod
    def _to_response(record: UserMemoryRecord) -> UserMemoryResponse:
        """
        将数据库记录转换为领域响应模型。

        :param record: PostgreSQL 长期记忆记录。
        :return: 长期记忆响应模型。
        """
        return UserMemoryResponse(
            id=record.id,
            type=MemoryType(record.memory_type),
            content=record.content,
            source=record.source,
            created_at=record.created_at.isoformat(),
        )