from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMCompletion:
    """一次大模型补全结果。"""

    content: str
    provider: str
    model: str


class LLMProvider(Protocol):
    """大模型服务端口。"""

    name: str
    model: str

    def complete(self, prompt: str) -> LLMCompletion:
        """
        根据提示词返回一次模型补全结果。

        :param prompt: 发送给大模型的完整提示词。
        :return: 包含回复内容、服务商和模型名称的补全结果。
        """
