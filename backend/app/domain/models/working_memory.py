from datetime import datetime, timezone
from enum import StrEnum
from typing import TypeAlias
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


MemoryMetadataValue: TypeAlias = str | int | float | bool | None


class WorkingMemoryKind(StrEnum):
    """工作记忆条目类型。"""

    MESSAGE = "message"
    TOOL_OBSERVATION = "tool_observation"


class ConversationRole(StrEnum):
    """对话消息角色。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class WorkingMemoryItem(BaseModel):
    """会话级工作记忆条目。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    kind: WorkingMemoryKind
    content: str = Field(min_length=1, max_length=4000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    role: ConversationRole | None = None
    tool_name: str | None = Field(default=None, min_length=1, max_length=100)
    metadata: dict[str, MemoryMetadataValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_kind_fields(self) -> "WorkingMemoryItem":
        """
        校验不同工作记忆类型要求的专用字段。

        :return: 已通过类型字段校验的工作记忆条目。
        """
        if self.kind is WorkingMemoryKind.MESSAGE and self.role is None:
            raise ValueError("message working memory requires role")
        if (
            self.kind is WorkingMemoryKind.TOOL_OBSERVATION
            and self.tool_name is None
        ):
            raise ValueError(
                "tool observation working memory requires tool_name"
            )
        return self


class WorkingMemoryListResponse(BaseModel):
    """指定会话的工作记忆列表响应。"""

    session_id: str
    items: list[WorkingMemoryItem]
