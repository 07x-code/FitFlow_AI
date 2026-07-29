"""为重构前的 Agent 服务接口保留向后兼容导入。

新代码应从 :mod:`app.agents.coach_agent` 导入。
"""

from app.agents.coach_agent import (
    CoachAgent,
    build_coach_chat_prompt,
    create_coach_agent,
)
from app.agents.tools.registry import ToolRegistry
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.infrastructure.user_memory_repository import UserMemoryRepository
from app.services.knowledge_retriever import KnowledgeRetriever
from app.services.llm_provider import LLMProvider


CoachChatService = CoachAgent
_build_coach_chat_prompt = build_coach_chat_prompt


def create_coach_chat_service(
    profile_repository: ProfileRepository,
    training_plan_repository: TrainingPlanRepository,
    llm_provider: LLMProvider | None = None,
    memory_repository: UserMemoryRepository | None = None,
    knowledge_retriever: KnowledgeRetriever | None = None,
    tool_registry: ToolRegistry | None = None,
) -> CoachChatService:
    return create_coach_agent(
        profile_repository=profile_repository,
        training_plan_repository=training_plan_repository,
        llm_provider=llm_provider,
        memory_repository=memory_repository,
        knowledge_retriever=knowledge_retriever,
        tool_registry=tool_registry,
    )
