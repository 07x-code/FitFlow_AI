from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MemoryType(StrEnum):
    """用户长期记忆类型。"""

    PREFERRED_EQUIPMENT = "preferred_equipment"
    DISLIKED_EXERCISE = "disliked_exercise"
    TRAINING_TIME = "training_time"
    PHYSICAL_LIMITATION = "physical_limitation"
    GENERAL_NOTE = "general_note"


class UserMemoryCreate(BaseModel):
    """创建用户长期记忆的输入。"""

    model_config = ConfigDict(extra="forbid")

    type: MemoryType
    content: str = Field(min_length=1, max_length=500)
    source: str = Field(default="user", pattern="^user$")


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
