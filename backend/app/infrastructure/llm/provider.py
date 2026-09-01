import json
from dataclasses import dataclass
from urllib import error, request

from app.core.config import AppSettings
from app.ports.llm import (
    LLMCompletion,
    LLMMessage,
    LLMProvider,
    LLMToolCall,
    LLMToolCompletion,
    LLMToolDefinition,
)


class FakeLLMProvider:
    """用于测试和本地演示的确定性大模型适配器。"""

    name = "fake"
    model = "offline-placeholder"

    def complete(self, prompt: str) -> LLMCompletion:
        """
        返回包含原始提示词的离线模拟结果。

        :param prompt: 待模拟处理的提示词。
        :return: 确定性的离线补全结果。
        """
        return LLMCompletion(
            content=f"离线模拟回复：{prompt}",
            provider=self.name,
            model=self.model,
        )

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: tuple[LLMToolDefinition, ...],
    ) -> LLMToolCompletion:
        """
        使用关键词规则模拟模型选择工具和生成最终回答。

        :param messages: 当前工具调用循环的消息。
        :param tools: 当前允许调用的工具。
        :return: 模拟的工具调用或最终文本结果。
        """
        if any(message.role == "tool" for message in messages):
            return self._final_tool_completion(messages)

        user_message = next(
            (
                message.content or ""
                for message in reversed(messages)
                if message.role == "user"
            ),
            "",
        )
        available_names = {tool.name for tool in tools}
        selected = _select_fake_tools(user_message, available_names)
        if not selected:
            return self._final_tool_completion(messages)

        calls = tuple(
            LLMToolCall(
                id=f"fake-tool-call-{index}",
                name=name,
                arguments=(
                    {"query": user_message, "limit": 3}
                    if name == "retrieve_fitness_knowledge"
                    else {}
                ),
            )
            for index, name in enumerate(selected, start=1)
        )
        return LLMToolCompletion(
            content=None,
            tool_calls=calls,
            provider=self.name,
            model=self.model,
        )

    def _final_tool_completion(
        self,
        messages: list[LLMMessage],
    ) -> LLMToolCompletion:
        """
        将当前消息上下文拼接为可断言的离线最终回复。

        :param messages: 当前工具调用循环的全部消息。
        :return: 不再包含工具调用的最终模拟结果。
        """
        context = "\n".join(
            message.content
            for message in messages
            if message.content
        )
        return LLMToolCompletion(
            content=f"离线模拟回复：{context}",
            tool_calls=(),
            provider=self.name,
            model=self.model,
        )


@dataclass(frozen=True)
class DryRunLLMProvider:
    """只展示配置状态、不访问网络的大模型适配器。"""

    name: str
    model: str

    def complete(self, prompt: str) -> LLMCompletion:
        """
        返回离线骨架模式说明。

        :param prompt: 原始提示词。
        :return: 不发起网络请求的补全结果。
        """
        return LLMCompletion(
            content=(
                f"{self.name} provider 已配置，但当前处于离线骨架模式，"
                f"不会发起真实网络请求。原始提示词：{prompt}"
            ),
            provider=self.name,
            model=self.model,
        )

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: tuple[LLMToolDefinition, ...],
    ) -> LLMToolCompletion:
        """
        返回不包含工具调用的离线结果。

        :param messages: 当前工具调用循环的消息。
        :param tools: 当前允许调用的工具。
        :return: 离线骨架模式的最终文本结果。
        """
        del tools
        content = "\n".join(
            message.content
            for message in messages
            if message.content
        )
        return LLMToolCompletion(
            content=(
                f"{self.name} provider 已配置，但当前处于离线骨架模式。"
                f"上下文：{content}"
            ),
            tool_calls=(),
            provider=self.name,
            model=self.model,
        )


@dataclass(frozen=True)
class DashScopeLLMProvider:
    """通过 OpenAI 兼容接口调用阿里云百炼千问。"""

    api_key: str
    model: str
    base_url: str
    timeout_seconds: int = 30

    name: str = "dashscope"

    def complete(self, prompt: str) -> LLMCompletion:
        """
        调用千问执行一次普通文本补全。

        :param prompt: 发送给千问的完整提示词。
        :return: 千问返回的普通补全结果。
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是 FitFlow AI 的健身教练，只能解释已经通过"
                        "安全规则的训练计划。"
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
        }
        response_body = self._post_chat_completion(payload)
        content = _extract_chat_completion_content(response_body)
        return LLMCompletion(
            content=content,
            provider=self.name,
            model=response_body.get("model", self.model),
        )

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: tuple[LLMToolDefinition, ...],
    ) -> LLMToolCompletion:
        """
        调用千问的 OpenAI 兼容工具调用接口。

        :param messages: 当前 Agent 运行中的标准消息。
        :param tools: 只允许千问选择的只读工具定义。
        :return: 千问返回的文本或结构化工具调用。
        """
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [_serialize_message(message) for message in messages],
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]
            payload["tool_choice"] = (
                "required"
                if any(tool.force_call for tool in tools)
                else "auto"
            )

        response_body = self._post_chat_completion(payload)
        content, tool_calls = _extract_tool_completion(response_body)
        return LLMToolCompletion(
            content=content,
            tool_calls=tool_calls,
            provider=self.name,
            model=response_body.get("model", self.model),
        )

    def _post_chat_completion(
        self,
        payload: dict[str, object],
    ) -> dict:
        """
        向千问兼容接口发送聊天补全请求。

        :param payload: 已序列化的聊天补全请求体。
        :return: 解析后的 JSON 响应对象。
        """
        http_request = request.Request(
            url=f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(
                http_request,
                timeout=self.timeout_seconds,
            ) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"{self.name} request failed with HTTP {exc.code}: {message}"
            ) from exc
        except (error.URLError, TimeoutError) as exc:
            raise RuntimeError(
                f"{self.name} request failed: {exc}"
            ) from exc

        if not isinstance(response_body, dict):
            raise RuntimeError(
                f"{self.name} response was not a JSON object."
            )
        return response_body


@dataclass(frozen=True)
class SiliconFlowLLMProvider(DashScopeLLMProvider):
    """通过 OpenAI 兼容接口调用硅基流动模型。"""

    name: str = "siliconflow"

    def _post_chat_completion(
        self,
        payload: dict[str, object],
    ) -> dict:
        """
        使用非思考模式调用硅基流动，缩短交互式请求耗时。

        :param payload: 已序列化的聊天补全请求体。
        :return: 解析后的 JSON 响应对象。
        """
        return super()._post_chat_completion(
            {
                **payload,
                "enable_thinking": False,
            }
        )


def _select_fake_tools(
    user_message: str,
    available_names: set[str],
) -> tuple[str, ...]:
    """
    根据用户问题选择离线测试所需的只读工具。

    :param user_message: 当前用户问题。
    :param available_names: 当前允许调用的工具名称。
    :return: 按固定顺序排列的工具名称。
    """
    lowered = user_message.lower()
    selected: list[str] = []
    keyword_groups = (
        (
            "get_latest_training_plan",
            ("plan", "计划", "今天练", "训练安排", "每周", "几天"),
        ),
        (
            "recall_user_memory",
            (
                "remember",
                "memory",
                "adapt",
                "personalize",
                "preference",
                "记得",
                "偏好",
                "调整",
                "适合我",
                "上次",
                "之前",
            ),
        ),
        (
            "retrieve_fitness_knowledge",
            ("rpe", "动作", "姿势", "怎么做", "训练原理", "热身", "恢复"),
        ),
    )
    for name, keywords in keyword_groups:
        if name in available_names and any(
            keyword in lowered for keyword in keywords
        ):
            selected.append(name)
    return tuple(selected)


def _serialize_message(message: LLMMessage) -> dict[str, object]:
    """
    将端口层标准消息转换为 OpenAI 兼容消息。

    :param message: 待转换的标准消息。
    :return: 可写入请求 JSON 的消息对象。
    """
    serialized: dict[str, object] = {"role": message.role}
    if message.content is not None:
        serialized["content"] = message.content
    if message.tool_call_id is not None:
        serialized["tool_call_id"] = message.tool_call_id
    if message.tool_calls:
        serialized["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(
                        call.arguments,
                        ensure_ascii=False,
                    ),
                },
            }
            for call in message.tool_calls
        ]
    return serialized


def _extract_tool_completion(
    response_body: dict,
) -> tuple[str | None, tuple[LLMToolCall, ...]]:
    """
    从 OpenAI 兼容响应中解析文本和工具调用。

    :param response_body: 千问返回的完整响应对象。
    :return: 可选文本和结构化工具调用元组。
    """
    try:
        message = response_body["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "DashScope response did not contain choices[0].message."
        ) from exc
    if not isinstance(message, dict):
        raise RuntimeError("DashScope response message was not an object.")

    content = message.get("content")
    if content is not None and not isinstance(content, str):
        raise RuntimeError("DashScope response content was not text.")

    calls: list[LLMToolCall] = []
    raw_calls = message.get("tool_calls") or []
    if not isinstance(raw_calls, list):
        raise RuntimeError("DashScope response tool_calls was not a list.")
    for raw_call in raw_calls:
        try:
            call_id = raw_call["id"]
            function = raw_call["function"]
            name = function["name"]
            raw_arguments = function.get("arguments", "{}")
        except (KeyError, TypeError) as exc:
            raise RuntimeError(
                "DashScope returned an invalid tool call."
            ) from exc

        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments or "{}")
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "DashScope returned invalid tool arguments JSON."
                ) from exc
        else:
            arguments = raw_arguments
        if not isinstance(arguments, dict):
            raise RuntimeError(
                "DashScope tool arguments must be a JSON object."
            )
        calls.append(
            LLMToolCall(
                id=str(call_id),
                name=str(name),
                arguments=arguments,
            )
        )

    if not calls and (not isinstance(content, str) or not content.strip()):
        raise RuntimeError("DashScope response content was empty.")
    return content, tuple(calls)


def _extract_chat_completion_content(response_body: dict) -> str:
    """
    从普通聊天补全响应中提取文本内容。

    :param response_body: 千问返回的完整响应对象。
    :return: 非空的回复文本。
    """
    content, tool_calls = _extract_tool_completion(response_body)
    if tool_calls or content is None:
        raise RuntimeError(
            "DashScope response did not contain a plain text completion."
        )
    return content


def create_llm_provider(
    settings: AppSettings | None = None,
) -> LLMProvider:
    """
    根据应用配置创建大模型适配器。

    :param settings: 可选的应用配置，默认从环境变量读取。
    :return: 与配置匹配的大模型适配器。
    """
    settings = settings or AppSettings.from_env()

    if settings.llm_provider == "fake":
        return FakeLLMProvider()

    if settings.llm_provider == "dashscope":
        if not settings.has_dashscope_api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY is required when "
                "FITFLOW_LLM_PROVIDER=dashscope."
            )
        return DashScopeLLMProvider(
            api_key=settings.dashscope_api_key,
            model=settings.dashscope_model,
            base_url=settings.dashscope_base_url,
        )

    if settings.llm_provider == "siliconflow":
        if not settings.has_siliconflow_api_key:
            raise ValueError(
                "SILICONFLOW_API_KEY is required when "
                "FITFLOW_LLM_PROVIDER=siliconflow."
            )
        return SiliconFlowLLMProvider(
            api_key=settings.siliconflow_api_key,
            model=settings.siliconflow_model,
            base_url=settings.siliconflow_base_url,
            timeout_seconds=60,
        )

    if settings.llm_provider == "openai":
        if not settings.has_openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when "
                "FITFLOW_LLM_PROVIDER=openai."
            )
        return DryRunLLMProvider(
            name="openai",
            model="openai-dry-run",
        )

    raise ValueError(
        "FITFLOW_LLM_PROVIDER must be one of: "
        "fake, dashscope, siliconflow, openai."
    )
