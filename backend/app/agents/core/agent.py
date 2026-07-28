from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.agents.core.message import AgentMessage


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass(frozen=True)
class AgentConfig:
    """Runtime behavior shared by all FitFlow agents.

    API agents are singletons, so conversation history is disabled by default
    to prevent one user's messages from leaking into another user's request.
    """

    keep_history: bool = False
    max_history_messages: int = 20

    def __post_init__(self) -> None:
        if self.max_history_messages < 1:
            raise ValueError("max_history_messages must be at least 1.")


class Agent(ABC, Generic[InputT, OutputT]):
    """Common execution contract inspired by HelloAgents' Agent base class."""

    def __init__(
        self,
        *,
        name: str,
        system_prompt: str | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.config = config or AgentConfig()
        self._history: list[AgentMessage] = []

    @abstractmethod
    def run(self, agent_input: InputT, **kwargs: object) -> OutputT:
        """Run the agent using its specialized input and output contract."""

    def add_message(self, message: AgentMessage) -> None:
        if not self.config.keep_history:
            return

        self._history.append(message)
        if len(self._history) > self.config.max_history_messages:
            self._history = self._history[-self.config.max_history_messages :]

    def record_exchange(self, user_content: str, assistant_content: str) -> None:
        self.add_message(AgentMessage(role="user", content=user_content))
        self.add_message(AgentMessage(role="assistant", content=assistant_content))

    def clear_history(self) -> None:
        self._history.clear()

    def get_history(self) -> tuple[AgentMessage, ...]:
        return tuple(self._history)
