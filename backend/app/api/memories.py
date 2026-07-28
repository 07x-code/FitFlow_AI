from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.domain.models import (
    UserMemoryCreate,
    UserMemoryListResponse,
    UserMemoryResponse,
)
from app.infrastructure.user_memory_repository import UserMemoryRepository


router = APIRouter(prefix="/api/memories", tags=["memories"])

memory_repository = UserMemoryRepository()


@router.post("", response_model=UserMemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    memory: UserMemoryCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> UserMemoryResponse:
    return memory_repository.create(user_id=user_id, memory=memory)


@router.get("", response_model=UserMemoryListResponse)
def list_memories(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> UserMemoryListResponse:
    return UserMemoryListResponse(memories=memory_repository.list_by_user(user_id))


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> None:
    deleted = memory_repository.delete_by_id_for_user(
        user_id=user_id,
        memory_id=memory_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")