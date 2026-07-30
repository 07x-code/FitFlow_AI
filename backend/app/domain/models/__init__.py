"""领域模型兼容导出入口。

新代码优先从具体模块导入；现有代码可继续使用
``from app.domain.models import ModelName``。
"""

from app.domain.models.coach import (
    CoachChatRequest,
    CoachChatResponse,
    FitnessKnowledgeItem,
    KnowledgeSource,
)
from app.domain.models.memory import (
    MemoryType,
    UserMemoryCreate,
    UserMemoryListResponse,
    UserMemoryResponse,
)
from app.domain.models.plan import (
    ExercisePrescription,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanDraftResponse,
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
    TrainingPlanHistoryResponse,
    WorkoutDayDraft,
)
from app.domain.models.profile import (
    FitnessGoal,
    FitnessProfileCreate,
    NutritionTargets,
    ProfileAssessmentResponse,
    RiskAssessment,
    Sex,
)
from app.domain.models.proposal import (
    ProposalDecision,
    ProposalDecisionRequest,
    ProposalListResponse,
    ProposalStatus,
    ProposalType,
    TrainingPlanProposalResponse,
)
from app.domain.models.report import WeeklyReportMetrics, WeeklyReportResponse
from app.domain.models.workout import (
    WorkoutHistoryResponse,
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
    WorkoutSetLog,
)

__all__ = [
    "CoachChatRequest",
    "CoachChatResponse",
    "ExercisePrescription",
    "FitnessGoal",
    "FitnessKnowledgeItem",
    "FitnessProfileCreate",
    "KnowledgeSource",
    "MemoryType",
    "NutritionTargets",
    "ProfileAssessmentResponse",
    "ProposalDecision",
    "ProposalDecisionRequest",
    "ProposalListResponse",
    "ProposalStatus",
    "ProposalType",
    "RiskAssessment",
    "SafetyCheckResult",
    "Sex",
    "TrainingPlanDraft",
    "TrainingPlanDraftResponse",
    "TrainingPlanExplanationResponse",
    "TrainingPlanHistoryItem",
    "TrainingPlanHistoryResponse",
    "TrainingPlanProposalResponse",
    "UserMemoryCreate",
    "UserMemoryListResponse",
    "UserMemoryResponse",
    "WeeklyReportMetrics",
    "WeeklyReportResponse",
    "WorkoutDayDraft",
    "WorkoutHistoryResponse",
    "WorkoutSafetyAlert",
    "WorkoutSessionCreate",
    "WorkoutSessionResponse",
    "WorkoutSetLog",
]
