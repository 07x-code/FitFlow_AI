from datetime import date

from dataclasses import dataclass

from app.application.errors import ConflictError, NotFoundError, UnprocessableError
from app.domain.models import (
    ProposalDecision,
    ProposalDecisionRequest,
    ProposalListResponse,
    ProposalStatus,
    SafetyCheckResult,
    TrainingPlanProposalResponse,
)
from app.domain.plan_generator import generate_beginner_plan
from app.domain.plan_schedule import get_next_week_start
from app.domain.risk_rules import assess_risk
from app.domain.training_rules import validate_beginner_plan
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanProposalRepositoryPort,
    TrainingPlanRepositoryPort,
)
DEFAULT_PLAN_TIMEZONE = "Asia/Shanghai"


@dataclass(frozen=True)
class ProposalUseCases:
    """训练计划提案应用用例。"""

    profiles: ProfileRepositoryPort
    proposals: TrainingPlanProposalRepositoryPort
    plans: TrainingPlanRepositoryPort

    async def create_training_plan(
        self,
        user_id: str,
    ) -> TrainingPlanProposalResponse:
        """
        生成经过安全检查、等待用户确认的训练计划提案。

        :param user_id: 用户标识。
        :return: 待确认的训练计划提案。
        """
        profile = await self.profiles.get(user_id)
        if profile is None:
            raise NotFoundError("Profile not found.")

        risk = assess_risk(profile)
        if risk["can_auto_plan"] is False:
            raise ConflictError(
                {
                    "message": "Automatic plan generation is blocked.",
                    "risk": risk,
                }
            )

        week_start = get_next_week_start(date.today())
        plan = generate_beginner_plan(
            profile,
            week_start=week_start,
            timezone=DEFAULT_PLAN_TIMEZONE,
            goal_summary=(
                f"围绕 {profile.goal.value} 目标安排下周训练。"
            ),
        )
        safety_check = SafetyCheckResult.model_validate(
            validate_beginner_plan(plan)
        )
        if safety_check.valid is False:
            raise UnprocessableError(
                {
                    "message": "Generated proposal failed safety check.",
                    "safety_check": safety_check.model_dump(),
                }
            )
        return await self.proposals.create(user_id, plan, safety_check)

    async def list(self, user_id: str) -> ProposalListResponse:
        """
        查询用户训练计划提案。

        :param user_id: 用户标识。
        :return: 用户提案列表响应。
        """
        return ProposalListResponse(
            proposals=await self.proposals.list_by_user(user_id)
        )

    async def get(
        self,
        user_id: str,
        proposal_id: int,
    ) -> TrainingPlanProposalResponse:
        """
        查询属于当前用户的训练计划提案。

        :param user_id: 用户标识。
        :param proposal_id: 提案标识。
        :return: 训练计划提案。
        """
        proposal = await self.proposals.get_by_id_for_user(user_id, proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal not found.")
        return proposal

    async def decide(
        self,
        user_id: str,
        proposal_id: int,
        request: ProposalDecisionRequest,
    ) -> TrainingPlanProposalResponse:
        """
        批准或拒绝训练计划 Proposal。

        :param user_id: 用户标识。
        :param proposal_id: Proposal 标识。
        :param request: 用户决策。
        :return: 更新后的 Proposal。
        """
        proposal = await self.get(user_id, proposal_id)
        if proposal.status != ProposalStatus.PENDING:
            raise ConflictError(
                "Proposal has already been decided."
            )

        if request.decision == ProposalDecision.REJECT:
            rejected = await self.proposals.reject(
                user_id=user_id,
                proposal_id=proposal_id,
                decision_note=request.decision_note,
            )
            if rejected is None:
                raise ConflictError(
                    "Proposal decision could not be completed."
                )

            return rejected

        approving = await self.proposals.mark_approving(
            user_id,
            proposal_id,
        )
        if approving is None:
            raise ConflictError(
                "Proposal approval is already in progress."
            )

        version = 1
        if approving.base_plan_id is not None:
            base_plan = await self.plans.get_by_id_for_user(
                user_id,
                approving.base_plan_id,
            )
            if base_plan is None:
                raise ConflictError(
                    "Base training plan is unavailable."
                )

            superseded = await self.plans.mark_superseded(
                user_id,
                base_plan.id,
            )
            if superseded is None:
                raise ConflictError(
                    "Base training plan cannot be replaced."
                )

            version = base_plan.version + 1

        approved_plan = await self.plans.save(
            user_id,
            approving.plan,
            approving.safety_check,
            source_proposal_id=approving.id,
            version=version,
        )

        approved = await self.proposals.approve(
            user_id=user_id,
            proposal_id=approving.id,
            approved_plan_id=approved_plan.id,
            decision_note=request.decision_note,
        )
        if approved is None:
            raise ConflictError(
                "Proposal approval could not be completed."
            )

        return approved
