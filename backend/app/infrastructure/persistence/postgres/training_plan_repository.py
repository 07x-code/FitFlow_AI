from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanHistoryItem,
    TrainingPlanStatus,
)
from app.infrastructure.persistence.postgres.models import TrainingPlanRecord


class TrainingPlanRepository:
    """PostgreSQL 正式训练计划仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        """
        创建正式训练计划仓储。

        :param session: 当前数据库操作使用的异步 Session。
        :return: 无返回值。
        """
        self._session = session

    async def save(
        self,
        user_id: str,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
        *,
        source_proposal_id: int,
        version: int,
    ) -> TrainingPlanHistoryItem:
        """
        保存由已批准 Proposal 生成的正式训练计划。

        :param user_id: 用户标识。
        :param plan: 已通过校验的训练计划草案。
        :param safety_check: 确定性安全检查结果。
        :param source_proposal_id: 来源 Proposal 标识。
        :param version: 同一用户同一周的计划版本。
        :return: 已保存的正式训练计划。
        """
        record = TrainingPlanRecord(
            user_id=user_id,
            week_start=plan.week_start,
            week_end=plan.week_end,
            timezone=plan.timezone,
            version=version,
            status=TrainingPlanStatus.SCHEDULED.value,
            source_proposal_id=source_proposal_id,
            plan_data=plan.model_dump(mode="json"),
            safety_check=safety_check.model_dump(mode="json"),
        )
        self._session.add(record)

        await self._session.flush()
        await self._session.refresh(record)

        return self._to_history_item(record)
    

    async def list_by_user(
        self,
        user_id: str,
    ) -> list[TrainingPlanHistoryItem]:
        """
        查询指定用户的正式训练计划历史。

        :param user_id: 用户标识。
        :return: 按创建时间和记录标识倒序排列的正式训练计划。
        """
        records = await self._session.scalars(
            select(TrainingPlanRecord)
            .where(TrainingPlanRecord.user_id == user_id)
            .order_by(
                TrainingPlanRecord.created_at.desc(),
                TrainingPlanRecord.id.desc(),
            )
        )

        return [
            self._to_history_item(record)
            for record in records
        ]


    async def get_by_id_for_user(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanHistoryItem | None:
        """
        按用户标识和计划标识查询正式训练计划。

        :param user_id: 用户标识。
        :param plan_id: 正式训练计划标识。
        :return: 匹配的正式训练计划；不存在或不属于该用户时返回 None。
        """
        record = await self._session.scalar(
            select(TrainingPlanRecord).where(
                TrainingPlanRecord.id == plan_id,
                TrainingPlanRecord.user_id == user_id,
            )
        )
        if record is None:
            return None

        return self._to_history_item(record)


    async def mark_superseded(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanHistoryItem | None:
        """
        将用户当前正式计划原子更新为已被替换。

        :param user_id: 用户标识。
        :param plan_id: 正式训练计划标识。
        :return: 更新后的正式计划；当前状态不允许更新时返回 None。
        """
        record = await self._session.scalar(
            update(TrainingPlanRecord)
            .where(
                TrainingPlanRecord.id == plan_id,
                TrainingPlanRecord.user_id == user_id,
                TrainingPlanRecord.status.in_(
                    (
                        TrainingPlanStatus.SCHEDULED.value,
                        TrainingPlanStatus.ACTIVE.value,
                    )
                ),
            )
            .values(
                status=TrainingPlanStatus.SUPERSEDED.value
            )
            .returning(TrainingPlanRecord)
        )
        if record is None:
            return None

        return self._to_history_item(record)

    @staticmethod
    def _to_history_item(
        record: TrainingPlanRecord,
    ) -> TrainingPlanHistoryItem:
        """
        将数据库记录转换为正式训练计划领域模型。

        :param record: PostgreSQL 正式训练计划记录。
        :return: 正式训练计划历史项。
        """
        return TrainingPlanHistoryItem(
            id=record.id,
            version=record.version,
            status=TrainingPlanStatus(record.status),
            source_proposal_id=record.source_proposal_id,
            plan=TrainingPlanDraft.model_validate(record.plan_data),
            safety_check=SafetyCheckResult.model_validate(
                record.safety_check
            ),
            created_at=record.created_at.isoformat(),
        )