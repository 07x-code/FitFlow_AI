from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
    WorkoutSetLog,
)
from app.infrastructure.persistence.postgres.models import (
    WorkoutSessionRecord,
)


class WorkoutSessionRepository:
    """PostgreSQL 训练记录仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        """
        创建训练记录仓储。

        :param session: 当前数据库操作使用的异步 Session。
        :return: 无返回值。
        """
        self._session = session

    async def save(
        self,
        user_id: str,
        plan_id: int,
        plan_day_name: str,
        session: WorkoutSessionCreate,
        safety_alert: WorkoutSafetyAlert | None,
    ) -> WorkoutSessionResponse:
        """
        保存一次训练记录。

        :param user_id: 用户标识。
        :param plan_id: 正式训练计划标识。
        :param plan_day_name: 对应的计划训练日名称。
        :param session: 待保存的训练记录。
        :param safety_alert: 根据训练反馈生成的安全提醒。
        :return: 已保存的训练记录。
        """
        record = WorkoutSessionRecord(
            user_id=user_id,
            plan_id=plan_id,
            plan_day_index=session.plan_day_index,
            plan_day_name=plan_day_name,
            completed=session.completed,
            fatigue_level=session.fatigue_level,
            pain_level=session.pain_level,
            notes=session.notes,
            sets_data=[
                workout_set.model_dump(mode="json")
                for workout_set in session.sets
            ],
            safety_alert=(
                safety_alert.model_dump(mode="json")
                if safety_alert is not None
                else None
            ),
        )
        self._session.add(record)

        await self._session.flush()
        await self._session.refresh(record)

        return self._to_response(record)

    

    async def list_by_user(
        self,
        user_id: str,
        plan_id: int | None = None,
    ) -> list[WorkoutSessionResponse]:
        """
        查询指定用户的训练记录。

        :param user_id: 用户标识。
        :param plan_id: 可选的正式训练计划筛选条件。
        :return: 按创建时间和记录标识倒序排列的训练记录。
        """
        statement = select(WorkoutSessionRecord).where(
            WorkoutSessionRecord.user_id == user_id
        )

        if plan_id is not None:
            statement = statement.where(
                WorkoutSessionRecord.plan_id == plan_id
            )

        records = await self._session.scalars(
            statement.order_by(
                WorkoutSessionRecord.created_at.desc(),
                WorkoutSessionRecord.id.desc(),
            )
        )

        return [
            self._to_response(record)
            for record in records
        ]
    

    async def list_by_user_in_period(
        self,
        user_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WorkoutSessionResponse]:
        """
        查询指定用户在时间区间内创建的训练记录。

        :param user_id: 用户标识。
        :param start_at: 包含在查询范围内的起始时间。
        :param end_at: 不包含在查询范围内的结束时间。
        :return: 按创建时间和记录标识倒序排列的训练记录。
        """
        if start_at.tzinfo is None or end_at.tzinfo is None:
            raise ValueError("start_at 和 end_at 必须包含时区。")

        if start_at >= end_at:
            raise ValueError("start_at 必须早于 end_at。")

        records = await self._session.scalars(
            select(WorkoutSessionRecord)
            .where(
                WorkoutSessionRecord.user_id == user_id,
                WorkoutSessionRecord.created_at >= start_at,
                WorkoutSessionRecord.created_at < end_at,
            )
            .order_by(
                WorkoutSessionRecord.created_at.desc(),
                WorkoutSessionRecord.id.desc(),
            )
        )

        return [
            self._to_response(record)
            for record in records
        ]
    
    @staticmethod
    def _to_response(
        record: WorkoutSessionRecord,
    ) -> WorkoutSessionResponse:
        """
        将 PostgreSQL 记录转换为训练记录响应。

        :param record: PostgreSQL 训练记录。
        :return: 训练记录响应。
        """
        safety_alert = None
        if record.safety_alert is not None:
            safety_alert = WorkoutSafetyAlert.model_validate(
                record.safety_alert
            )

        return WorkoutSessionResponse(
            id=record.id,
            plan_id=record.plan_id,
            plan_day_index=record.plan_day_index,
            plan_day_name=record.plan_day_name,
            completed=record.completed,
            fatigue_level=record.fatigue_level,
            pain_level=record.pain_level,
            notes=record.notes,
            sets=[
                WorkoutSetLog.model_validate(workout_set)
                for workout_set in record.sets_data
            ],
            safety_alert=safety_alert,
            created_at=record.created_at.isoformat(),
        )