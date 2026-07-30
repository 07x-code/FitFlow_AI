from enum import StrEnum

from pydantic import BaseModel, Field

from app.domain.models.plan import SafetyCheckResult, TrainingPlanDraft


class ProposalType(StrEnum):
    """人工确认提案类型。"""

    TRAINING_PLAN = "training_plan"


class ProposalStatus(StrEnum):
    """人工确认提案状态。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProposalDecision(StrEnum):
    """用户对提案的决策。"""

    APPROVE = "approve"
    REJECT = "reject"


class ProposalDecisionRequest(BaseModel):
    """用户提交的提案决策。"""

    decision: ProposalDecision
    decision_note: str | None = Field(default=None, max_length=500)


class TrainingPlanProposalResponse(BaseModel):
    """训练计划提案响应。"""

    id: int
    type: ProposalType
    status: ProposalStatus
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    approved_plan_id: int | None = None
    decision_note: str | None = None
    created_at: str
    decided_at: str | None = None


class ProposalListResponse(BaseModel):
    """用户提案列表响应。"""

    proposals: list[TrainingPlanProposalResponse]
