import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _load_env_file(path: str | Path = DEFAULT_ENV_PATH) -> None:
    """
    加载简单的 KEY=VALUE 配置，且不覆盖终端中已有的环境变量。

    :param path: 环境变量文件路径，默认指向 backend/.env。
    :return: 无返回值。
    """

    env_path = Path(path)
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()

        name, separator, value = line.partition("=")
        name = name.strip()
        if not separator or not name or not name.replace("_", "").isalnum():
            continue

        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(name, value)


_load_env_file()


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
