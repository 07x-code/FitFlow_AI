from dataclasses import dataclass
from typing import Protocol

from app.core.config import AppSettings


@dataclass(frozen=True)
class LLMCompletion:
    content: str
    provider: str
    model: str


class LLMProvider(Protocol):
    name: str
    model: str

    def complete(self, prompt: str) -> LLMCompletion:
        """Return one completion for a prompt."""


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


def create_llm_provider(settings: AppSettings | None = None) -> LLMProvider:
    settings = settings or AppSettings.from_env()

    if settings.llm_provider == "fake":
        return FakeLLMProvider()

    if settings.llm_provider == "dashscope":
        if not settings.has_dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is required when FITFLOW_LLM_PROVIDER=dashscope.")
        return DryRunLLMProvider(name="dashscope", model="qwen-dry-run")

    if settings.llm_provider == "openai":
        if not settings.has_openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when FITFLOW_LLM_PROVIDER=openai.")
        return DryRunLLMProvider(name="openai", model="openai-dry-run")

    raise ValueError(
        "FITFLOW_LLM_PROVIDER must be one of: fake, dashscope, openai."
    )
