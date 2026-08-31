from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from app.domain.models.plan import SafetyCheckResult, TrainingPlanDraft


class ProposalType(StrEnum):
    """人工确认提案类型。"""

    TRAINING_PLAN = "training_plan"


class ProposalOperation(StrEnum):
    """训练计划 Proposal 操作类型。"""

    CREATE = "create"
    REPLACE = "replace"
    ADJUST = "adjust"


class ProposalStatus(StrEnum):
    """人工确认提案状态。"""

    PENDING = "pending"
    APPROVING = "approving"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"

def can_transition_proposal_status(
    current: ProposalStatus,
    target: ProposalStatus,
) -> bool:
    """
    判断训练计划 Proposal 是否允许进行指定状态转换。

    :param current: 当前 Proposal 状态。
    :param target: 目标 Proposal 状态。
    :return: 状态转换符合领域规则时返回 True。
    """
    if current == ProposalStatus.PENDING:
        return target in {
            ProposalStatus.APPROVING,
            ProposalStatus.REJECTED,
            ProposalStatus.SUPERSEDED,
        }

    if current == ProposalStatus.APPROVING:
        return target == ProposalStatus.APPROVED

    return False


class ProposalDecision(StrEnum):
    """用户对提案的决策。"""

    APPROVE = "approve"
    REJECT = "reject"


class ProposalDecisionRequest(BaseModel):
    """用户提交的提案决策。"""

    decision: ProposalDecision
    decision_note: str | None = Field(default=None, max_length=500)


class ProposalRevisionRequest(BaseModel):
    """用户提交的训练计划修改意见。"""

    feedback: str = Field(min_length=2, max_length=500)


class TrainingPlanProposalResponse(BaseModel):
    """训练计划提案响应。"""

    id: int
    type: ProposalType
    operation: ProposalOperation
    target_week_start: date
    base_plan_id: int | None = Field(default=None, gt=0)
    parent_proposal_id: int | None = Field(default=None, gt=0)
    revision: int = Field(ge=1)
    status: ProposalStatus
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    generation_summary: str = Field(min_length=1, max_length=1000)
    approved_plan_id: int | None = None
    decision_note: str | None = None
    created_at: str
    decided_at: str | None = None


class ProposalListResponse(BaseModel):
    """用户提案列表响应。"""

    proposals: list[TrainingPlanProposalResponse]
