from dataclasses import dataclass, field
from typing import Any, Literal, Mapping


MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class AgentMessage:
    """One framework-neutral message in an agent conversation."""

    role: MessageRole
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
