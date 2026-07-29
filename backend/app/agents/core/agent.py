from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.agents.core.message import AgentMessage


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass(frozen=True)
class AgentConfig:
    """所有 FitFlow Agent 共享的运行时配置。

    API 中的 Agent 以单例方式运行，因此默认关闭进程内对话历史，
    防止不同用户的消息在请求之间发生泄漏。
    """

    keep_history: bool = False
    max_history_messages: int = 20

    def __post_init__(self) -> None:
        if self.max_history_messages < 1:
            raise ValueError("max_history_messages must be at least 1.")


class Agent(ABC, Generic[InputT, OutputT]):
    """参考 HelloAgents 的 Agent 基类定义通用执行契约。"""

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
        """
        按照当前 Agent 的专用输入输出契约执行任务。

        :param agent_input: 当前 Agent 需要处理的输入。
        :param kwargs: 具体 Agent 可选的扩展参数。
        :return: 当前 Agent 的执行结果。
        """

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
