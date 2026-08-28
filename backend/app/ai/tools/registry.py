from typing import Any, Callable
from inspect import isawaitable

from app.ai.tools.base import FunctionTool, Tool, ToolParameter


class ToolNotFoundError(LookupError):
    pass


class DuplicateToolError(ValueError):
    pass


class ToolRegistry:
    """通过稳定名称注册、发现并执行 Agent 能力。"""

    def __init__(self) -> None:
        self._tools: dict[str, Tool[Any, Any]] = {}

    def register(
        self,
        tool: Tool[Any, Any],
        *,
        replace: bool = False,
    ) -> Tool[Any, Any]:
        if tool.name in self._tools and not replace:
            raise DuplicateToolError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool
        return tool

    def register_function(
        self,
        *,
        name: str,
        description: str,
        function: Callable[[Any], Any],
        parameters: tuple[ToolParameter, ...] = (),
        replace: bool = False,
    ) -> Tool[Any, Any]:
        return self.register(
            FunctionTool(
                name=name,
                description=description,
                function=function,
                parameters=parameters,
            ),
            replace=replace,
        )

    def get(self, name: str) -> Tool[Any, Any]:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"Tool '{name}' is not registered.") from exc

    def execute(self, name: str, tool_input: Any) -> Any:
        return self.get(name).run(tool_input)

    async def execute_async(
        self,
        name: str,
        tool_input: Any,
    ) -> Any:
        """
        执行工具，并等待工具返回的异步结果。

        同步领域工具可以继续直接返回结果，异步 Repository
        工具返回的协程会在这里等待完成。

        :param name: 工具名称。
        :param tool_input: 工具输入。
        :return: 工具最终执行结果。
        """
        result = self.execute(name, tool_input)
        if isawaitable(result):
            return await result
        return result

    def list_tools(self) -> tuple[Tool[Any, Any], ...]:
        return tuple(self._tools.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def describe_tools(self) -> str:
        if not self._tools:
            return "No tools registered."

        return "\n".join(tool.describe() for tool in self._tools.values())
