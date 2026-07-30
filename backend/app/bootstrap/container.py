from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.ai.agents.single.coach import create_coach_agent
from app.ai.agents.single.planner import create_training_plan_agent
from app.application.use_cases import (
    CoachUseCases,
    MemoryUseCases,
    ProfileUseCases,
    ProposalUseCases,
    ReportUseCases,
    TrainingPlanUseCases,
    WorkoutUseCases,
)
from app.core.config import AppSettings
from app.infrastructure.profile_repository import DEFAULT_DB_PATH, ProfileRepository
from app.infrastructure.proposal_repository import TrainingPlanProposalRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.infrastructure.user_memory_repository import UserMemoryRepository
from app.infrastructure.workout_repository import WorkoutSessionRepository
from app.services.coach_explainer import create_coach_explainer
from app.services.knowledge_retriever import KnowledgeRetriever
from app.services.llm_provider import create_llm_provider


@dataclass(frozen=True)
class ApplicationContainer:
    """应用运行所需的完整用例容器。"""

    profiles: ProfileUseCases
    training_plans: TrainingPlanUseCases
    memories: MemoryUseCases
    coach: CoachUseCases
    proposals: ProposalUseCases
    workouts: WorkoutUseCases
    reports: ReportUseCases


def create_container(
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    settings: AppSettings | None = None,
) -> ApplicationContainer:
    """
    创建并连接 Repository、Agent 与应用用例。

    :param db_path: SQLite 数据库路径。
    :param settings: 可选的应用配置，默认从环境变量读取。
    :return: 已完成依赖装配的应用容器。
    """
    settings = settings or AppSettings.from_env()

    profile_repository = ProfileRepository(db_path)
    training_plan_repository = TrainingPlanRepository(db_path)
    memory_repository = UserMemoryRepository(db_path)
    proposal_repository = TrainingPlanProposalRepository(db_path)
    workout_repository = WorkoutSessionRepository(db_path)
    knowledge_retriever = KnowledgeRetriever.from_default_file()
    llm_provider = create_llm_provider(settings)

    training_plan_agent = create_training_plan_agent(
        profile_repository=profile_repository,
        training_plan_repository=training_plan_repository,
    )
    coach_agent = create_coach_agent(
        profile_repository=profile_repository,
        training_plan_repository=training_plan_repository,
        memory_repository=memory_repository,
        knowledge_retriever=knowledge_retriever,
        llm_provider=llm_provider,
    )
    coach_explainer = create_coach_explainer(settings)

    return ApplicationContainer(
        profiles=ProfileUseCases(profile_repository),
        training_plans=TrainingPlanUseCases(
            repository=training_plan_repository,
            agent=training_plan_agent,
            explainer=coach_explainer,
        ),
        memories=MemoryUseCases(memory_repository),
        coach=CoachUseCases(coach_agent),
        proposals=ProposalUseCases(
            profiles=profile_repository,
            proposals=proposal_repository,
            plans=training_plan_repository,
        ),
        workouts=WorkoutUseCases(
            plans=training_plan_repository,
            sessions=workout_repository,
        ),
        reports=ReportUseCases(
            plans=training_plan_repository,
            sessions=workout_repository,
            proposals=proposal_repository,
        ),
    )


@lru_cache(maxsize=1)
def get_container() -> ApplicationContainer:
    """
    返回进程内共享的应用容器。

    :return: 已缓存的应用容器。
    """
    return create_container()
