from dataclasses import dataclass
from functools import lru_cache

from app.ai.services.training_plan_explainer import (
    create_training_plan_explainer,
)
from app.application.use_cases import WorkingMemoryUseCases
from app.core.config import AppSettings
from app.infrastructure.knowledge.retriever import KnowledgeRetriever
from app.infrastructure.llm.provider import create_llm_provider
from app.infrastructure.memory.factory import create_working_memory_store
from app.ports.ai import TrainingPlanExplainerPort
from app.ports.knowledge import KnowledgeRetrieverPort
from app.ports.llm import LLMProvider
from app.ports.working_memory import WorkingMemoryStorePort


@dataclass(frozen=True)
class ApplicationContainer:
    """应用进程内共享组件容器。"""

    knowledge_retriever: KnowledgeRetrieverPort
    llm_provider: LLMProvider
    training_plan_explainer: TrainingPlanExplainerPort
    working_memory_store: WorkingMemoryStorePort
    working_memory: WorkingMemoryUseCases


def create_container(
    *,
    settings: AppSettings | None = None,
) -> ApplicationContainer:
    """
    创建应用进程内共享组件。

    :param settings: 可选的应用配置，默认从环境变量读取。
    :return: 已完成装配的共享组件容器。
    """
    settings = settings or AppSettings.from_env()

    knowledge_retriever = KnowledgeRetriever.from_default_file()
    llm_provider = create_llm_provider(settings)
    working_memory_store = create_working_memory_store(settings)

    return ApplicationContainer(
        knowledge_retriever=knowledge_retriever,
        llm_provider=llm_provider,
        training_plan_explainer=create_training_plan_explainer(
            llm_provider
        ),
        working_memory_store=working_memory_store,
        working_memory=WorkingMemoryUseCases(working_memory_store),
    )


@lru_cache(maxsize=1)
def get_container() -> ApplicationContainer:
    """
    返回进程内共享的应用组件容器。

    :return: 已缓存的共享组件容器。
    """
    return create_container()