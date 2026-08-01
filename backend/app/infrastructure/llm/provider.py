import json
from dataclasses import dataclass
from urllib import error, request

from app.core.config import AppSettings
from app.ports.llm import LLMCompletion, LLMProvider


class FakeLLMProvider:
    name = "fake"
    model = "offline-placeholder"

    def complete(self, prompt: str) -> LLMCompletion:
        return LLMCompletion(
            content=f"离线模拟回复：{prompt}",
            provider=self.name,
            model=self.model,
        )


@dataclass(frozen=True)
class DryRunLLMProvider:
    name: str
    model: str

    def complete(self, prompt: str) -> LLMCompletion:
        return LLMCompletion(
            content=(
                f"{self.name} provider 已配置，但当前处于离线骨架模式，"
                f"不会发起真实网络请求。原始提示词：{prompt}"
            ),
            provider=self.name,
            model=self.model,
        )


@dataclass(frozen=True)
class DashScopeLLMProvider:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: int = 30

    name: str = "dashscope"

    def complete(self, prompt: str) -> LLMCompletion:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是 FitFlow AI 的健身教练，只能解释已经通过安全规则的训练计划。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
        }
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
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DashScope request failed with HTTP {exc.code}: {message}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"DashScope request failed: {exc.reason}") from exc

        content = _extract_chat_completion_content(response_body)
        return LLMCompletion(
            content=content,
            provider=self.name,
            model=response_body.get("model", self.model),
        )


def _extract_chat_completion_content(response_body: dict) -> str:
    try:
        content = response_body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("DashScope response did not contain choices[0].message.content.") from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("DashScope response content was empty.")

    return content


def create_llm_provider(settings: AppSettings | None = None) -> LLMProvider:
    settings = settings or AppSettings.from_env()

    if settings.llm_provider == "fake":
        return FakeLLMProvider()

    if settings.llm_provider == "dashscope":
        if not settings.has_dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is required when FITFLOW_LLM_PROVIDER=dashscope.")
        return DashScopeLLMProvider(
            api_key=settings.dashscope_api_key,
            model=settings.dashscope_model,
            base_url=settings.dashscope_base_url,
        )

    if settings.llm_provider == "openai":
        if not settings.has_openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when FITFLOW_LLM_PROVIDER=openai.")
        return DryRunLLMProvider(name="openai", model="openai-dry-run")

    raise ValueError(
        "FITFLOW_LLM_PROVIDER must be one of: fake, dashscope, openai."
    )
