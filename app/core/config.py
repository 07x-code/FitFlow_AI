import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    llm_provider: str
    dashscope_api_key: str | None
    openai_api_key: str | None
    dashscope_model: str
    dashscope_base_url: str

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            llm_provider=_read_env("FITFLOW_LLM_PROVIDER", default="fake").lower(),
            dashscope_api_key=_read_env("DASHSCOPE_API_KEY"),
            openai_api_key=_read_env("OPENAI_API_KEY"),
            dashscope_model=_read_env("DASHSCOPE_MODEL", default="qwen-plus"),
            dashscope_base_url=_read_env(
                "DASHSCOPE_BASE_URL",
                default="https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
        )

    @property
    def has_dashscope_api_key(self) -> bool:
        return bool(self.dashscope_api_key)

    @property
    def has_openai_api_key(self) -> bool:
        return bool(self.openai_api_key)


def _read_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None

    value = value.strip()
    return value or None
