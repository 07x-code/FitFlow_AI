"""领域模型统一导出入口。

具体模型按数据类型放在当前目录；调用方既可以从具体模块导入，
也可以使用 ``from app.domain.models import ModelName``。
"""

from app.domain.models.coach import (
    CoachChatRequest,
    CoachChatResponse,
    FitnessKnowledgeItem,
    KnowledgeSource,
)
from app.domain.models.plan import (
    ExercisePrescription,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanDraftResponse,
    TrainingPlanExplanationResponse,
    TrainingPlanStatus,
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
    ProposalOperation,
    ProposalRevisionRequest,
    ProposalStatus,
    ProposalType,
    TrainingPlanProposalResponse,
)
from app.domain.models.report import WeeklyReportMetrics, WeeklyReportResponse
from app.domain.models.user_memory import (
    MemoryType,
    UserMemoryCreate,
    UserMemoryListResponse,
    UserMemoryResponse,
)
from app.domain.models.working_memory import (
    ConversationRole,
    WorkingMemoryItem,
    WorkingMemoryKind,
    WorkingMemoryListResponse,
)
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
    "ConversationRole",
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
    "ProposalOperation",
    "ProposalRevisionRequest",
    "ProposalStatus",
    "ProposalType",
    "RiskAssessment",
    "SafetyCheckResult",
    "Sex",
    "TrainingPlanDraft",
    "TrainingPlanDraftResponse",
    "TrainingPlanExplanationResponse",
    "TrainingPlanStatus",
    "TrainingPlanHistoryItem",
    "TrainingPlanHistoryResponse",
    "TrainingPlanProposalResponse",
    "UserMemoryCreate",
    "UserMemoryListResponse",
    "UserMemoryResponse",
    "WeeklyReportMetrics",
    "WeeklyReportResponse",
    "WorkingMemoryItem",
    "WorkingMemoryKind",
    "WorkingMemoryListResponse",
    "WorkoutDayDraft",
    "WorkoutHistoryResponse",
    "WorkoutSafetyAlert",
    "WorkoutSessionCreate",
    "WorkoutSessionResponse",
    "WorkoutSetLog",
    
]
