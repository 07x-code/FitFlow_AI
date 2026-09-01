from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FitnessKnowledgeItem(BaseModel):
    """本地健身知识条目。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    content: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class KnowledgeSource(BaseModel):
    """AI 教练回答引用的知识来源。"""

    title: str
    category: str
    summary: str


class CoachChatRequest(BaseModel):
    """AI 教练对话请求。"""

    message: str = Field(min_length=1, max_length=1000)


class MemoryMutationEvent(BaseModel):
    """本轮对话实际执行的长期记忆变更。"""

    action: Literal["remembered", "forgotten"]
    memory_id: int
    type: str
    content: str


class CoachChatResponse(BaseModel):
    """AI 教练对话响应。"""

    answer: str
    safety_level: str
    referenced_plan_id: int | None = None
    knowledge_sources: list[KnowledgeSource] = Field(default_factory=list)
    memory_events: list[MemoryMutationEvent] = Field(default_factory=list)
