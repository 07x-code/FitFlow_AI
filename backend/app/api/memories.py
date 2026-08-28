from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import (
    get_memory_use_cases,
    get_working_memory_use_cases,
)
from app.application.use_cases import MemoryUseCases, WorkingMemoryUseCases
from app.domain.models import WorkingMemoryListResponse
from app.domain.models import (
    UserMemoryCreate,
    UserMemoryListResponse,
    UserMemoryResponse,
)


router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.post("", response_model=UserMemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory: UserMemoryCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[MemoryUseCases, Depends(get_memory_use_cases)],
) -> UserMemoryResponse:
    """
    创建当前用户的显式长期记忆。

    :param memory: 待创建的长期记忆。
    :param user_id: 用户标识。
    :param use_cases: 长期记忆应用用例。
    :return: 已创建的长期记忆。
    """
    return await use_cases.create(user_id, memory)


@router.get("", response_model=UserMemoryListResponse)
async def list_memories(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[MemoryUseCases, Depends(get_memory_use_cases)],
) -> UserMemoryListResponse:
    """
    列出当前用户的显式长期记忆。

    :param user_id: 用户标识。
    :param use_cases: 长期记忆应用用例。
    :return: 当前用户的长期记忆列表。
    """
    return await use_cases.list(user_id)


@router.get(
    "/working/{session_id}",
    response_model=WorkingMemoryListResponse,
)
def list_working_memory(
    session_id: str,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[
        WorkingMemoryUseCases,
        Depends(get_working_memory_use_cases),
    ],
) -> WorkingMemoryListResponse:
    """
    读取当前用户指定会话的工作记忆。

    :param session_id: 会话标识。
    :param user_id: 用户标识。
    :param use_cases: 工作记忆应用用例。
    :return: 指定会话的工作记忆列表。
    """
    return use_cases.list(user_id, session_id)


@router.delete(
    "/working/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def end_working_memory_session(
    session_id: str,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[
        WorkingMemoryUseCases,
        Depends(get_working_memory_use_cases),
    ],
) -> None:
    """
    结束当前用户的指定会话并清理工作记忆。

    :param session_id: 会话标识。
    :param user_id: 用户标识。
    :param use_cases: 工作记忆应用用例。
    :return: 无返回值。
    """
    use_cases.end_session(user_id, session_id)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[MemoryUseCases, Depends(get_memory_use_cases)],
) -> None:
    """
    删除当前用户拥有的显式长期记忆。

    :param memory_id: 长期记忆标识。
    :param user_id: 用户标识。
    :param use_cases: 长期记忆应用用例。
    :return: 无返回值。
    """
    await use_cases.delete(user_id, memory_id)
