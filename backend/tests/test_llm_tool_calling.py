import json

from app.infrastructure.llm.provider import DashScopeLLMProvider
from app.ports.llm import LLMMessage, LLMToolDefinition


def test_dashscope_provider_sends_tools_and_parses_tool_calls(monkeypatch):
    """
    验证千问适配器发送工具定义并解析结构化工具调用。

    :param monkeypatch: Pytest 提供的运行时替换工具。
    :return: 无返回值。
    """
    captured: dict[str, object] = {}

    class FakeHTTPResponse:
        """模拟 urllib 返回的聊天补全响应。"""

        def __enter__(self):
            """
            进入响应上下文。

            :return: 当前模拟响应对象。
            """
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            """
            退出响应上下文。

            :param exc_type: 上下文中的异常类型。
            :param exc_value: 上下文中的异常对象。
            :param traceback: 上下文中的异常堆栈。
            :return: 不抑制异常。
            """
            return None

        def read(self) -> bytes:
            """
            返回包含工具调用的响应 JSON。

            :return: UTF-8 编码的模拟响应体。
            """
            return json.dumps(
                {
                    "model": "qwen-plus",
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call-1",
                                        "type": "function",
                                        "function": {
                                            "name": (
                                                "retrieve_fitness_knowledge"
                                            ),
                                            "arguments": (
                                                '{"query":"RPE","limit":2}'
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                },
                ensure_ascii=False,
            ).encode("utf-8")

    def fake_urlopen(http_request, timeout):
        """
        捕获请求体并返回模拟响应。

        :param http_request: urllib 请求对象。
        :param timeout: 请求超时秒数。
        :return: 模拟 HTTP 响应。
        """
        captured["timeout"] = timeout
        captured["body"] = json.loads(
            http_request.data.decode("utf-8")
        )
        return FakeHTTPResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    provider = DashScopeLLMProvider(
        api_key="dashscope-test-key",
        model="qwen-plus",
        base_url="https://dashscope.example/compatible-mode/v1",
    )

    completion = provider.complete_with_tools(
        messages=[
            LLMMessage(role="system", content="系统规则"),
            LLMMessage(role="user", content="RPE 是什么？"),
        ],
        tools=(
            LLMToolDefinition(
                name="retrieve_fitness_knowledge",
                description="检索健身知识。",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
            ),
        ),
    )

    body = captured["body"]
    assert isinstance(body, dict)
    assert body["tool_choice"] == "auto"
    assert body["tools"][0]["function"]["name"] == (
        "retrieve_fitness_knowledge"
    )
    assert completion.content is None
    assert completion.tool_calls[0].name == "retrieve_fitness_knowledge"
    assert completion.tool_calls[0].arguments == {
        "query": "RPE",
        "limit": 2,
    }


def test_dashscope_provider_can_require_a_tool_call(monkeypatch) -> None:
    """
    验证指定工具可要求兼容接口必须返回工具调用。

    :param monkeypatch: Pytest 提供的运行时替换工具。
    :return: 无返回值。
    """
    captured: dict[str, object] = {}

    def fake_post_chat_completion(self, payload):
        """
        捕获模型请求并返回空文本结果。

        :param self: 当前大模型适配器。
        :param payload: 待发送的兼容接口请求体。
        :return: 模拟聊天补全响应。
        """
        del self
        captured.update(payload)
        return {
            "model": "qwen-plus",
            "choices": [
                {"message": {"content": "无候选", "tool_calls": []}}
            ],
        }

    monkeypatch.setattr(
        DashScopeLLMProvider,
        "_post_chat_completion",
        fake_post_chat_completion,
    )
    provider = DashScopeLLMProvider(
        api_key="dashscope-test-key",
        model="qwen-plus",
        base_url="https://dashscope.example/compatible-mode/v1",
    )

    provider.complete_with_tools(
        messages=[LLMMessage(role="user", content="提取记忆")],
        tools=(
            LLMToolDefinition(
                name="extract_memory",
                description="提取长期记忆。",
                parameters={"type": "object", "properties": {}},
                force_call=True,
            ),
        ),
    )

    assert captured["tool_choice"] == "required"
