"""应用核心使用的抽象端口。"""

from app.ports.ai import (
    CoachAgentPort,
    TrainingPlanAgentPort,
    TrainingPlanAgentResultPort,
    TrainingPlanExplainerPort,
)
from app.ports.knowledge import KnowledgeRetrieverPort
from app.ports.llm import LLMCompletion, LLMProvider
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanProposalRepositoryPort,
    TrainingPlanRepositoryPort,
    UserMemoryRepositoryPort,
    WorkoutSessionRepositoryPort,
)

__all__ = [
    "CoachAgentPort",
    "KnowledgeRetrieverPort",
    "LLMCompletion",
    "LLMProvider",
    "ProfileRepositoryPort",
    "TrainingPlanAgentPort",
    "TrainingPlanAgentResultPort",
    "TrainingPlanExplainerPort",
    "TrainingPlanProposalRepositoryPort",
    "TrainingPlanRepositoryPort",
    "UserMemoryRepositoryPort",
    "WorkoutSessionRepositoryPort",
]
