import pytest
import asyncio
from app.ai.core import Agent, AgentConfig
from app.ai.tools import (
    DuplicateToolError,
    ToolNotFoundError,
    ToolRegistry,
)


class EchoAgent(Agent[str, str]):
    def run(self, agent_input: str, **kwargs: object) -> str:
        response = f"echo: {agent_input}"
        self.record_exchange(agent_input, response)
        return response


def test_agent_history_is_disabled_for_shared_api_agents_by_default():
    agent = EchoAgent(name="echo")

    assert agent.run("hello") == "echo: hello"
    assert agent.get_history() == ()


def test_agent_history_can_be_enabled_and_bounded():
    agent = EchoAgent(
        name="echo",
        config=AgentConfig(keep_history=True, max_history_messages=2),
    )

    agent.run("first")
    agent.run("second")

    history = agent.get_history()
    assert [message.content for message in history] == [
        "second",
        "echo: second",
    ]


def test_tool_registry_registers_describes_and_executes_functions():
    registry = ToolRegistry()
    registry.register_function(
        name="double",
        description="Double an integer.",
        function=lambda value: value * 2,
    )

    assert registry.names() == ("double",)
    assert registry.execute("double", 4) == 8
    assert registry.describe_tools() == "- double: Double an integer."


def test_tool_registry_rejects_accidental_duplicate_names():
    registry = ToolRegistry()
    registry.register_function(
        name="echo",
        description="Echo input.",
        function=lambda value: value,
    )

    with pytest.raises(DuplicateToolError, match="already registered"):
        registry.register_function(
            name="echo",
            description="Another echo.",
            function=lambda value: value,
        )


def test_tool_registry_reports_unknown_tools():
    with pytest.raises(ToolNotFoundError, match="missing"):
        ToolRegistry().execute("missing", None)

def test_tool_registry_executes_sync_and_async_tools_asynchronously():
    """
    验证异步执行入口兼容同步工具和异步工具。

    :return: 无返回值。
    """
    registry = ToolRegistry()

    async def async_double(value: int) -> int:
        """
        异步计算输入值的两倍。

        :param value: 输入整数。
        :return: 输入值的两倍。
        """
        return value * 2

    registry.register_function(
        name="sync-double",
        description="Synchronously double an integer.",
        function=lambda value: value * 2,
    )
    registry.register_function(
        name="async-double",
        description="Asynchronously double an integer.",
        function=async_double,
    )

    async def run_assertions() -> None:
        """
        执行同步和异步工具断言。

        :return: 无返回值。
        """
        assert await registry.execute_async("sync-double", 4) == 8
        assert await registry.execute_async("async-double", 4) == 8

    asyncio.run(run_assertions())