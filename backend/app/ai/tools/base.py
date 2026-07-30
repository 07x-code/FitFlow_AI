from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass(frozen=True)
class ToolParameter:
    name: str
    description: str
    type_name: str = "string"
    required: bool = True
    default: Any = None


class Tool(ABC, Generic[InputT, OutputT]):
    """表示一个可发现、可直接执行的能力。"""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        parameters: tuple[ToolParameter, ...] = (),
    ) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    def run(self, tool_input: InputT) -> OutputT:
        """
        执行该工具。

        :param tool_input: 工具执行所需的输入。
        :return: 工具执行结果。
        """

    def describe(self) -> str:
        if not self.parameters:
            return f"- {self.name}: {self.description}"

        parameter_text = ", ".join(
            f"{parameter.name}: {parameter.type_name}"
            + ("" if parameter.required else " (optional)")
            for parameter in self.parameters
        )
        return f"- {self.name}({parameter_text}): {self.description}"


class FunctionTool(Tool[InputT, OutputT]):
    """用于把小型函数注册为工具的适配器。"""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        function: Callable[[InputT], OutputT],
        parameters: tuple[ToolParameter, ...] = (),
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            parameters=parameters,
        )
        self._function = function

    def run(self, tool_input: InputT) -> OutputT:
        return self._function(tool_input)
