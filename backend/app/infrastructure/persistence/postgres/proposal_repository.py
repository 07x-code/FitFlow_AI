from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    ProposalOperation,
    ProposalStatus,
    ProposalType,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanProposalResponse,
)
from app.infrastructure.persistence.postgres.models import (
    TrainingPlanProposalRecord,
    TrainingPlanRecord,
)


class TrainingPlanProposalRepository:
    """PostgreSQL 训练计划 Proposal 仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        """
        创建训练计划 Proposal 仓储。

        :param session: 当前数据库操作使用的异步 Session。
        :return: 无返回值。
        """
        self._session = session

    async def create(
        self,
        user_id: str,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanProposalResponse:
        """
        创建等待用户决定的训练计划 Proposal。

        :param user_id: 用户标识。
        :param plan: 已通过校验的训练计划草案。
        :param safety_check: 确定性安全检查结果。
        :return: 已创建的训练计划 Proposal。
        """
        record = TrainingPlanProposalRecord(
            user_id=user_id,
            proposal_type=ProposalType.TRAINING_PLAN.value,
            operation=ProposalOperation.CREATE.value,
            target_week_start=plan.week_start,
            revision=1,
            status=ProposalStatus.PENDING.value,
            plan_snapshot=plan.model_dump(mode="json"),
            safety_check=safety_check.model_dump(mode="json"),
            generation_summary=plan.goal_summary,
        )
        self._session.add(record)

        await self._session.flush()
        await self._session.refresh(record)

        return self._to_response(record)

    

    async def list_by_user(
        self,
        user_id: str,
    ) -> list[TrainingPlanProposalResponse]:
        """
        查询指定用户的训练计划 Proposal。

        :param user_id: 用户标识。
        :return: 按创建时间和记录标识倒序排列的 Proposal 列表。
        """
        records = await self._session.scalars(
            select(TrainingPlanProposalRecord)
            .where(TrainingPlanProposalRecord.user_id == user_id)
            .order_by(
                TrainingPlanProposalRecord.created_at.desc(),
                TrainingPlanProposalRecord.id.desc(),
            )
        )

        return [
            self._to_response(record)
            for record in records
        ]



    async def get_by_id_for_user(
        self,
        user_id: str,
        proposal_id: int,
    ) -> TrainingPlanProposalResponse | None:
        """
        按用户标识和 Proposal 标识查询训练计划 Proposal。

        :param user_id: 用户标识。
        :param proposal_id: Proposal 标识。
        :return: 匹配的 Proposal；不存在或不属于该用户时返回 None。
        """
        record = await self._session.scalar(
            select(TrainingPlanProposalRecord).where(
                TrainingPlanProposalRecord.id == proposal_id,
                TrainingPlanProposalRecord.user_id == user_id,
            )
        )
        if record is None:
            return None

        return self._to_response(record)


    async def mark_approving(
        self,
        user_id: str,
        proposal_id: int,
    ) -> TrainingPlanProposalResponse | None:
        """
        将待决定 Proposal 原子更新为批准处理中。

        :param user_id: 用户标识。
        :param proposal_id: Proposal 标识。
        :return: 更新后的 Proposal;当前状态不允许更新时返回 None。
        """
        record = await self._session.scalar(
            update(TrainingPlanProposalRecord)
            .where(
                TrainingPlanProposalRecord.id == proposal_id,
                TrainingPlanProposalRecord.user_id == user_id,
                TrainingPlanProposalRecord.status
                == ProposalStatus.PENDING.value,
            )
            .values(status=ProposalStatus.APPROVING.value)
            .returning(TrainingPlanProposalRecord)
        )
        if record is None:
            return None

        return self._to_response(record)




    async def approve(
        self,
        user_id: str,
        proposal_id: int,
        approved_plan_id: int,
        decision_note: str | None,
    ) -> TrainingPlanProposalResponse | None:
        """
        将批准处理中的 Proposal 更新为已批准并关联正式计划。

        :param user_id: 用户标识。
        :param proposal_id: Proposal 标识。
        :param approved_plan_id: 根据 Proposal 创建的正式计划标识。
        :param decision_note: 用户批准备注。
        :return: 已批准的 Proposal；当前状态不允许更新时返回 None。
        """
        record = await self._session.scalar(
            update(TrainingPlanProposalRecord)
            .where(
                TrainingPlanProposalRecord.id == proposal_id,
                TrainingPlanProposalRecord.user_id == user_id,
                TrainingPlanProposalRecord.status
                == ProposalStatus.APPROVING.value,
            )
            .values(
                status=ProposalStatus.APPROVED.value,
                approved_plan_id=approved_plan_id,
                decision_note=decision_note,
                decided_at=func.now(),
            )
            .returning(TrainingPlanProposalRecord)
        )
        if record is None:
            return None

        return self._to_response(record)



    async def reject(
        self,
        user_id: str,
        proposal_id: int,
        decision_note: str | None,
    ) -> TrainingPlanProposalResponse | None:
        """
        将待决定 Proposal 更新为已拒绝。

        :param user_id: 用户标识。
        :param proposal_id: Proposal 标识。
        :param decision_note: 用户拒绝原因。
        :return: 已拒绝的 Proposal；当前状态不允许更新时返回 None。
        """
        record = await self._session.scalar(
            update(TrainingPlanProposalRecord)
            .where(
                TrainingPlanProposalRecord.id == proposal_id,
                TrainingPlanProposalRecord.user_id == user_id,
                TrainingPlanProposalRecord.status
                == ProposalStatus.PENDING.value,
            )
            .values(
                status=ProposalStatus.REJECTED.value,
                decision_note=decision_note,
                decided_at=func.now(),
            )
            .returning(TrainingPlanProposalRecord)
        )
        if record is None:
            return None

        return self._to_response(record)



    async def create_revision(
        self,
        user_id: str,
        parent_proposal_id: int,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanProposalResponse | None:
        """
        根据待决定 Proposal 创建下一版修订。

        :param user_id: 用户标识。
        :param parent_proposal_id: 被修订的 Proposal 标识。
        :param plan: 修订后的训练计划草案。
        :param safety_check: 修订计划的确定性安全检查结果。
        :return: 新版本 Proposal；原 Proposal 不可修订时返回 None。
        """
        parent = await self._session.scalar(
            update(TrainingPlanProposalRecord)
            .where(
                TrainingPlanProposalRecord.id == parent_proposal_id,
                TrainingPlanProposalRecord.user_id == user_id,
                TrainingPlanProposalRecord.status
                == ProposalStatus.PENDING.value,
                TrainingPlanProposalRecord.target_week_start
                == plan.week_start,
            )
            .values(
                status=ProposalStatus.SUPERSEDED.value,
                decided_at=func.now(),
            )
            .returning(TrainingPlanProposalRecord)
        )
        if parent is None:
            return None

        record = TrainingPlanProposalRecord(
            user_id=user_id,
            proposal_type=ProposalType.TRAINING_PLAN.value,
            operation=ProposalOperation.ADJUST.value,
            target_week_start=plan.week_start,
            base_plan_id=parent.base_plan_id,
            parent_proposal_id=parent.id,
            revision=parent.revision + 1,
            status=ProposalStatus.PENDING.value,
            plan_snapshot=plan.model_dump(mode="json"),
            safety_check=safety_check.model_dump(mode="json"),
            generation_summary=plan.goal_summary,
        )
        self._session.add(record)

        await self._session.flush()
        await self._session.refresh(record)

        return self._to_response(record)




    async def create_replacement(
        self,
        user_id: str,
        base_plan_id: int,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanProposalResponse | None:
        """
        基于用户已有的正式计划创建替换 Proposal。

        :param user_id: 用户标识。
        :param base_plan_id: 被替换的正式计划标识。
        :param plan: 替换后的训练计划草案。
        :param safety_check: 替换计划的确定性安全检查结果。
        :return: 待决定的替换 Proposal；基础计划不匹配时返回 None。
        """
        base_plan = await self._session.scalar(
            select(TrainingPlanRecord).where(
                TrainingPlanRecord.id == base_plan_id,
                TrainingPlanRecord.user_id == user_id,
                TrainingPlanRecord.week_start == plan.week_start,
            )
        )
        if base_plan is None:
            return None

        record = TrainingPlanProposalRecord(
            user_id=user_id,
            proposal_type=ProposalType.TRAINING_PLAN.value,
            operation=ProposalOperation.REPLACE.value,
            target_week_start=plan.week_start,
            base_plan_id=base_plan.id,
            parent_proposal_id=None,
            revision=1,
            status=ProposalStatus.PENDING.value,
            plan_snapshot=plan.model_dump(mode="json"),
            safety_check=safety_check.model_dump(mode="json"),
            generation_summary=plan.goal_summary,
        )
        self._session.add(record)

        await self._session.flush()
        await self._session.refresh(record)

        return self._to_response(record)
    
    @staticmethod
    def _to_response(
        record: TrainingPlanProposalRecord,
    ) -> TrainingPlanProposalResponse:
        """
        将 PostgreSQL 记录转换为 Proposal 领域响应。

        :param record: PostgreSQL Proposal 记录。
        :return: 训练计划 Proposal 响应。
        """
        decided_at = None
        if record.decided_at is not None:
            decided_at = record.decided_at.isoformat()

        return TrainingPlanProposalResponse(
            id=record.id,
            type=ProposalType(record.proposal_type),
            operation=ProposalOperation(record.operation),
            target_week_start=record.target_week_start,
            base_plan_id=record.base_plan_id,
            parent_proposal_id=record.parent_proposal_id,
            revision=record.revision,
            status=ProposalStatus(record.status),
            plan=TrainingPlanDraft.model_validate(record.plan_snapshot),
            safety_check=SafetyCheckResult.model_validate(
                record.safety_check
            ),
            generation_summary=record.generation_summary,
            approved_plan_id=record.approved_plan_id,
            decision_note=record.decision_note,
            created_at=record.created_at.isoformat(),
            decided_at=decided_at,
        )