from dataclasses import dataclass
from typing import Any, Literal, Protocol


LLMMessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class LLMCompletion:
    """一次普通大模型补全结果。"""

    content: str
    provider: str
    model: str


@dataclass(frozen=True)
class LLMToolCall:
    """大模型生成的一次结构化工具调用。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMMessage:
    """工具调用循环中的标准消息。"""

    role: LLMMessageRole
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: tuple[LLMToolCall, ...] = ()


@dataclass(frozen=True)
class LLMToolDefinition:
    """提供给大模型的只读工具定义。"""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class LLMToolCompletion:
    """一次支持工具调用的大模型补全结果。"""

    content: str | None
    tool_calls: tuple[LLMToolCall, ...]
    provider: str
    model: str


class LLMProvider(Protocol):
    """大模型服务端口。"""

    name: str
    model: str

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: tuple[LLMToolDefinition, ...],
    ) -> LLMToolCompletion:
        """
        根据消息和工具定义执行一次工具调用补全。

        :param messages: 当前 Agent 运行中的消息列表。
        :param tools: 允许大模型选择的只读工具定义。
        :return: 模型文本或结构化工具调用结果。
        """

    def complete(self, prompt: str) -> LLMCompletion:
        """
        根据提示词返回一次模型补全结果。

        :param prompt: 发送给大模型的完整提示词。
        :return: 包含回复内容、服务商和模型名称的补全结果。
        """
