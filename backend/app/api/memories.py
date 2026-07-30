from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import get_memory_use_cases
from app.application.use_cases.memories import MemoryUseCases
from app.domain.models import (
    UserMemoryCreate,
    UserMemoryListResponse,
    UserMemoryResponse,
)


router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.post("", response_model=UserMemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    memory: UserMemoryCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[MemoryUseCases, Depends(get_memory_use_cases)],
) -> UserMemoryResponse:
    return use_cases.create(user_id, memory)


@router.get("", response_model=UserMemoryListResponse)
def list_memories(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[MemoryUseCases, Depends(get_memory_use_cases)],
) -> UserMemoryListResponse:
    return use_cases.list(user_id)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[MemoryUseCases, Depends(get_memory_use_cases)],
) -> None:
    use_cases.delete(user_id, memory_id)
