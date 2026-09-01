from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MemoryType(StrEnum):
    """用户长期记忆类型。"""

    PREFERRED_EQUIPMENT = "preferred_equipment"
    DISLIKED_EXERCISE = "disliked_exercise"
    TRAINING_TIME = "training_time"
    PHYSICAL_LIMITATION = "physical_limitation"
    GENERAL_NOTE = "general_note"


class MemoryCommandAction(StrEnum):
    """从用户消息识别出的长期记忆操作。"""

    REMEMBER = "remember"
    FORGET = "forget"


class MemoryCandidate(BaseModel):
    """大模型从用户消息中提取的长期记忆候选。"""

    model_config = ConfigDict(extra="forbid")

    action: MemoryCommandAction
    type: MemoryType
    value: str = Field(min_length=1, max_length=80)
    evidence: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)
    is_explicit: bool
    is_temporary: bool


class UserMemoryCreate(BaseModel):
    """创建用户长期记忆的输入。"""

    model_config = ConfigDict(extra="forbid")

    type: MemoryType
    content: str = Field(min_length=1, max_length=500)
    source: str = Field(default="user", pattern="^user$")
    memory_key: str | None = Field(default=None, min_length=1, max_length=160)


class MemoryCommand(BaseModel):
    """经过程序安全规则校验的长期记忆命令。"""

    model_config = ConfigDict(extra="forbid")

    action: MemoryCommandAction
    type: MemoryType
    memory_key: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=500)


class UserMemoryResponse(BaseModel):
    """单条用户长期记忆响应。"""

    id: int
    type: MemoryType
    content: str
    source: str
    created_at: str


class UserMemoryListResponse(BaseModel):
    """用户长期记忆列表响应。"""

    memories: list[UserMemoryResponse]
