from sqlalchemy.ext.asyncio import AsyncSession

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
from app.bootstrap.container import ApplicationContainer
from app.infrastructure.persistence.postgres.profile_repository import (
    ProfileRepository,
)
from app.infrastructure.persistence.postgres.proposal_repository import (
    TrainingPlanProposalRepository,
)
from app.infrastructure.persistence.postgres.training_plan_repository import (
    TrainingPlanRepository,
)
from app.infrastructure.persistence.postgres.user_memory_repository import (
    UserMemoryRepository,
)
from app.infrastructure.persistence.postgres.workout_session_repository import (
    WorkoutSessionRepository,
)


def create_profile_use_cases(
    session: AsyncSession,
) -> ProfileUseCases:
    """
    创建请求级用户画像用例。

    :param session: 当前请求共享的数据库 Session。
    :return: 用户画像应用用例。
    """
    return ProfileUseCases(ProfileRepository(session))


def create_proposal_use_cases(
    session: AsyncSession,
) -> ProposalUseCases:
    """
    创建请求级 Proposal 用例。

    :param session: 当前请求共享的数据库 Session。
    :return: Proposal 应用用例。
    """
    return ProposalUseCases(
        profiles=ProfileRepository(session),
        proposals=TrainingPlanProposalRepository(session),
        plans=TrainingPlanRepository(session),
    )


def create_training_plan_use_cases(
    session: AsyncSession,
    shared: ApplicationContainer,
) -> TrainingPlanUseCases:
    """
    创建请求级训练计划用例。

    :param session: 当前请求共享的数据库 Session。
    :param shared: 应用共享组件容器。
    :return: 训练计划应用用例。
    """
    profile_repository = ProfileRepository(session)

    return TrainingPlanUseCases(
        repository=TrainingPlanRepository(session),
        agent=create_training_plan_agent(
            profile_repository=profile_repository,
        ),
        explainer=shared.training_plan_explainer,
    )


def create_memory_use_cases(
    session: AsyncSession,
) -> MemoryUseCases:
    """
    创建请求级长期记忆用例。

    :param session: 当前请求共享的数据库 Session。
    :return: 长期记忆应用用例。
    """
    return MemoryUseCases(UserMemoryRepository(session))


def create_coach_use_cases(
    session: AsyncSession,
    shared: ApplicationContainer,
) -> CoachUseCases:
    """
    创建请求级 AI 教练用例。

    :param session: 当前请求共享的数据库 Session。
    :param shared: 应用共享组件容器。
    :return: AI 教练应用用例。
    """
    return CoachUseCases(
        agent=create_coach_agent(
            profile_repository=ProfileRepository(session),
            training_plan_repository=TrainingPlanRepository(session),
            memory_repository=UserMemoryRepository(session),
            knowledge_retriever=shared.knowledge_retriever,
            llm_provider=shared.llm_provider,
            working_memory=shared.working_memory_store,
        )
    )


def create_workout_use_cases(
    session: AsyncSession,
) -> WorkoutUseCases:
    """
    创建请求级训练记录用例。

    :param session: 当前请求共享的数据库 Session。
    :return: 训练记录应用用例。
    """
    return WorkoutUseCases(
        plans=TrainingPlanRepository(session),
        sessions=WorkoutSessionRepository(session),
    )


def create_report_use_cases(
    session: AsyncSession,
) -> ReportUseCases:
    """
    创建请求级训练周报用例。

    :param session: 当前请求共享的数据库 Session。
    :return: 训练周报应用用例。
    """
    return ReportUseCases(
        plans=TrainingPlanRepository(session),
        sessions=WorkoutSessionRepository(session),
        proposals=TrainingPlanProposalRepository(session),
    )