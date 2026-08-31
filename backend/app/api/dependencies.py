from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases import (
    CoachUseCases,
    MemoryUseCases,
    ProfileUseCases,
    ProposalUseCases,
    ReportUseCases,
    TrainingPlanUseCases,
    WorkingMemoryUseCases,
    WorkoutUseCases,
)
from app.bootstrap.container import get_container
from app.bootstrap.request_scope import (
    create_coach_use_cases,
    create_memory_use_cases,
    create_profile_use_cases,
    create_proposal_use_cases,
    create_report_use_cases,
    create_training_plan_use_cases,
    create_workout_use_cases,
)


async def get_database_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    为当前请求提供共享的 PostgreSQL 异步 Session。

    :param request: 当前 FastAPI 请求。
    :return: 当前请求使用的异步 Session。
    """
    session_factory = request.app.state.session_factory

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_profile_use_cases(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session, scope="function"),
    ],
) -> ProfileUseCases:
    """
    获取绑定当前请求 Session 的用户画像应用用例。

    :param session: 当前请求共享的异步数据库 Session。
    :return: 用户画像应用用例。
    """
    return create_profile_use_cases(session)

def get_proposal_use_cases(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session, scope="function"),
    ],
) -> ProposalUseCases:
    """
    获取绑定当前请求 Session 的 Proposal 应用用例。

    :param session: 当前请求共享的异步数据库 Session。
    :return: Proposal 应用用例。
    """
    return create_proposal_use_cases(session, get_container())


def get_training_plan_use_cases(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session, scope="function"),
    ],
) -> TrainingPlanUseCases:
    """
    获取绑定当前请求 Session 的训练计划应用用例。

    :param session: 当前请求共享的异步数据库 Session。
    :return: 训练计划应用用例。
    """


    return create_training_plan_use_cases(
        session,
        get_container(),
    )


def get_memory_use_cases(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session, scope="function"),
    ],
) -> MemoryUseCases:
    """
    获取绑定当前请求 Session 的长期记忆应用用例。

    :param session: 当前请求共享的异步数据库 Session。
    :return: 长期记忆应用用例。
    """
    return create_memory_use_cases(session)

def get_working_memory_use_cases() -> WorkingMemoryUseCases:
    """
    获取工作记忆应用用例。

    :return: 工作记忆应用用例。
    """
    return get_container().working_memory


def get_coach_use_cases(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session, scope="function"),
    ],
) -> CoachUseCases:
    """
    获取绑定当前请求 Session 的 AI 教练应用用例。

    :param session: 当前请求共享的异步数据库 Session。
    :return: AI 教练应用用例。
    """
    shared = get_container()

    return create_coach_use_cases(
        session,
        shared,
    )



def get_workout_use_cases(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session, scope="function"),
    ],
) -> WorkoutUseCases:
    """
    获取绑定当前请求 Session 的训练记录应用用例。

    :param session: 当前请求共享的异步数据库 Session。
    :return: 训练记录应用用例。
    """
    return create_workout_use_cases(session)


def get_report_use_cases(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session, scope="function"),
    ],
) -> ReportUseCases:
    """
    获取绑定当前请求 Session 的训练周报应用用例。

    :param session: 当前请求共享的异步数据库 Session。
    :return: 训练周报应用用例。
    """
    return create_report_use_cases(session)
