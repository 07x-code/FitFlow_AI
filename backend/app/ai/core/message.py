from dataclasses import dataclass, field
from typing import Any, Literal, Mapping


MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class AgentMessage:
    """表示 Agent 对话中的一条框架无关消息。"""

    role: MessageRole
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
