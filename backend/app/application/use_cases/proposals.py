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
from app.domain.risk_rules import assess_risk
from app.domain.training_rules import validate_beginner_plan
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanProposalRepositoryPort,
    TrainingPlanRepositoryPort,
)


@dataclass(frozen=True)
class ProposalUseCases:
    """训练计划提案应用用例。"""

    profiles: ProfileRepositoryPort
    proposals: TrainingPlanProposalRepositoryPort
    plans: TrainingPlanRepositoryPort

    def create_training_plan(
        self,
        user_id: str,
    ) -> TrainingPlanProposalResponse:
        """
        生成经过安全检查、等待用户确认的训练计划提案。

        :param user_id: 用户标识。
        :return: 待确认的训练计划提案。
        """
        profile = self.profiles.get(user_id)
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

        plan = generate_beginner_plan(profile)
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
        return self.proposals.create(user_id, plan, safety_check)

    def list(self, user_id: str) -> ProposalListResponse:
        """
        查询用户训练计划提案。

        :param user_id: 用户标识。
        :return: 用户提案列表响应。
        """
        return ProposalListResponse(
            proposals=self.proposals.list_by_user(user_id)
        )

    def get(
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
        proposal = self.proposals.get_by_id_for_user(user_id, proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal not found.")
        return proposal

    def decide(
        self,
        user_id: str,
        proposal_id: int,
        request: ProposalDecisionRequest,
    ) -> TrainingPlanProposalResponse:
        """
        批准或拒绝训练计划提案。

        :param user_id: 用户标识。
        :param proposal_id: 提案标识。
        :param request: 用户决策。
        :return: 更新后的训练计划提案。
        """
        proposal = self.get(user_id, proposal_id)
        if proposal.status != ProposalStatus.PENDING:
            raise ConflictError("Proposal has already been decided.")

        if request.decision == ProposalDecision.APPROVE:
            approved_plan = self.plans.save(
                user_id,
                proposal.plan,
                proposal.safety_check,
            )
            updated = self.proposals.approve(
                user_id=user_id,
                proposal_id=proposal_id,
                approved_plan_id=approved_plan.id,
                decision_note=request.decision_note,
            )
        else:
            updated = self.proposals.reject(
                user_id=user_id,
                proposal_id=proposal_id,
                decision_note=request.decision_note,
            )

        if updated is None:
            raise NotFoundError("Proposal not found.")
        return updated
