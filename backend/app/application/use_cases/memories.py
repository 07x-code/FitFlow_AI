from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.application.errors import NotFoundError
from app.domain.models import (
    MemoryCommandAction,
    MemoryMutationEvent,
    UserMemoryCreate,
    UserMemoryListResponse,
    UserMemoryResponse,
)
from app.ai.services.long_term_memory_extractor import extract_memory_candidates
from app.domain.policies.long_term_memory import (
    extract_memory_commands,
    validate_memory_candidates,
)
from app.ports.llm import LLMProvider
from app.ports.repositories import UserMemoryRepositoryPort


@dataclass(frozen=True)
class MemoryUseCases:
    """用户长期记忆应用用例。"""

    repository: UserMemoryRepositoryPort
    llm: LLMProvider | None = None

    async def create(
        self,
        user_id: str,
        memory: UserMemoryCreate,
    ) -> UserMemoryResponse:
        """
        创建用户长期记忆。

        :param user_id: 用户标识。
        :param memory: 待保存的记忆。
        :return: 已保存的记忆。
        """
        return await self.repository.create(user_id=user_id, memory=memory)

    async def list(self, user_id: str) -> UserMemoryListResponse:
        """
        查询用户长期记忆。

        :param user_id: 用户标识。
        :return: 用户长期记忆列表响应。
        """
        memories = await self.repository.list_by_user(user_id)
        return UserMemoryListResponse(
            memories=memories
        )

    async def capture_explicit(
        self,
        user_id: str,
        message: str,
    ) -> list[MemoryMutationEvent]:
        """
        从当前用户消息中保存或忘记明确的长期训练记忆。

        :param user_id: 用户标识。
        :param message: 当前用户发送的原始消息。
        :return: 本轮实际执行的长期记忆变更事件。
        """
        commands = extract_memory_commands(message)
        if self.llm is not None:
            candidates = await asyncio.to_thread(
                extract_memory_candidates,
                self.llm,
                message,
            )
            if candidates is not None:
                commands = validate_memory_candidates(message, candidates)

        events: list[MemoryMutationEvent] = []
        for command in commands:
            if command.action is MemoryCommandAction.FORGET:
                forgotten = await self.repository.forget_by_key(
                    user_id,
                    command.type.value,
                    command.memory_key,
                )
                if forgotten is not None:
                    events.append(
                        MemoryMutationEvent(
                            action="forgotten",
                            memory_id=forgotten.id,
                            type=command.type,
                            content=command.content,
                        )
                    )
                continue

            remembered = await self.repository.upsert_by_key(
                user_id,
                UserMemoryCreate(
                    type=command.type,
                    content=command.content,
                    source="user",
                    memory_key=command.memory_key,
                ),
            )
            if remembered is not None:
                events.append(
                    MemoryMutationEvent(
                        action="remembered",
                        memory_id=remembered.id,
                        type=remembered.type,
                        content=remembered.content,
                    )
                )
        return events

    async def delete(self, user_id: str, memory_id: int) -> None:
        """
        删除属于当前用户的长期记忆。

        :param user_id: 用户标识。
        :param memory_id: 记忆标识。
        :return: 无返回值。
        """
        deleted = await self.repository.delete_by_id_for_user(
            user_id=user_id,
            memory_id=memory_id,
        )
        if not deleted:
            raise NotFoundError("Memory not found.")
