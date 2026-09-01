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
            memory_key=memory.memory_key,
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

    async def upsert_by_key(
        self,
        user_id: str,
        memory: UserMemoryCreate,
    ) -> UserMemoryResponse | None:
        """
        按规范化键新增或更新一条 active 长期记忆。

        :param user_id: 用户标识。
        :param memory: 包含规范化键的长期记忆。
        :return: 发生新增或内容更新时返回记忆；内容未变化时返回 None。
        """
        if memory.memory_key is None:
            raise ValueError("memory_key is required for memory upsert")

        record = await self._get_active_by_key(
            user_id,
            memory.type.value,
            memory.memory_key,
        )
        if record is None:
            return await self.create(user_id, memory)
        if record.content == memory.content:
            return None

        record.content = memory.content
        record.source = memory.source
        await self._session.flush()
        await self._session.refresh(record)
        return self._to_response(record)

    async def forget_by_key(
        self,
        user_id: str,
        memory_type: str,
        memory_key: str,
    ) -> UserMemoryResponse | None:
        """
        按规范化键软删除一条 active 长期记忆。

        :param user_id: 用户标识。
        :param memory_type: 长期记忆类型。
        :param memory_key: 规范化记忆键。
        :return: 已停用的记忆；不存在时返回 None。
        """
        record = await self._get_active_by_key(
            user_id,
            memory_type,
            memory_key,
        )
        if record is None:
            return None

        record.status = "deleted"
        await self._session.flush()
        await self._session.refresh(record)
        return self._to_response(record)


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
            UserMemoryRecord.status == "active",
        )
        record = await self._session.scalar(statement)

        if record is None:
            return False

        record.status = "deleted"
        await self._session.flush()
        return True

    async def _get_active_by_key(
        self,
        user_id: str,
        memory_type: str,
        memory_key: str,
    ) -> UserMemoryRecord | None:
        """
        查询指定用户和规范化键对应的 active 长期记忆。

        :param user_id: 用户标识。
        :param memory_type: 长期记忆类型。
        :param memory_key: 规范化记忆键。
        :return: 匹配的数据库记录；不存在时返回 None。
        """
        statement = select(UserMemoryRecord).where(
            UserMemoryRecord.user_id == user_id,
            UserMemoryRecord.memory_type == memory_type,
            UserMemoryRecord.memory_key == memory_key,
            UserMemoryRecord.status == "active",
        )
        return await self._session.scalar(statement)
    

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
