import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://fitflow:fitflow@127.0.0.1:5432/fitflow_dev"
)

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+asyncpg://fitflow:fitflow@127.0.0.1:5432/fitflow_test"
)


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
    siliconflow_api_key: str | None = None
    siliconflow_model: str = "Qwen/Qwen3.5-4B"
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    database_url: str = DEFAULT_DATABASE_URL
    test_database_url: str = DEFAULT_TEST_DATABASE_URL
    working_memory_backend: str = "memory"
    redis_url: str = "redis://127.0.0.1:6379/0"
    working_memory_ttl_seconds: int = 7200
    working_memory_capacity: int = 40

    @classmethod
    def from_env(cls) -> "AppSettings":
        """
        从环境变量创建应用配置。

        :return: 已解析的应用配置。
        """
        database_url = _read_env(
            "FITFLOW_DATABASE_URL",
            default=DEFAULT_DATABASE_URL,
        )
        if database_url is None:
            raise ValueError("FITFLOW_DATABASE_URL must not be empty")


        test_database_url = _read_env(
            "FITFLOW_TEST_DATABASE_URL",
            default=DEFAULT_TEST_DATABASE_URL,
        )
        if test_database_url is None:
            raise ValueError("FITFLOW_TEST_DATABASE_URL must not be empty")
        
        return cls(
            
            llm_provider=_read_env("FITFLOW_LLM_PROVIDER", default="fake").lower(),
            dashscope_api_key=_read_env("DASHSCOPE_API_KEY"),
            openai_api_key=_read_env("OPENAI_API_KEY"),
            dashscope_model=_read_env("DASHSCOPE_MODEL", default="qwen-plus"),
            dashscope_base_url=_read_env(
                "DASHSCOPE_BASE_URL",
                default="https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            siliconflow_api_key=_read_env("SILICONFLOW_API_KEY"),
            siliconflow_model=_read_env(
                "SILICONFLOW_MODEL",
                default="Qwen/Qwen3.5-4B",
            ),
            siliconflow_base_url=_read_env(
                "SILICONFLOW_BASE_URL",
                default="https://api.siliconflow.cn/v1",
            ),
            database_url=database_url,
            test_database_url=test_database_url,
            working_memory_backend=_read_env(
                "FITFLOW_WORKING_MEMORY_BACKEND",
                default="memory",
            ).lower(),
            redis_url=_read_env(
                "FITFLOW_REDIS_URL",
                default="redis://127.0.0.1:6379/0",
            ),
            working_memory_ttl_seconds=_read_positive_int(
                "FITFLOW_WORKING_MEMORY_TTL_SECONDS",
                default=7200,
            ),
            working_memory_capacity=_read_positive_int(
                "FITFLOW_WORKING_MEMORY_CAPACITY",
                default=40,
            ),
        )

    @property
    def has_dashscope_api_key(self) -> bool:
        """
        判断是否已配置 DashScope API Key。

        :return: 已配置时返回 True，否则返回 False。
        """
        return bool(self.dashscope_api_key)

    @property
    def has_openai_api_key(self) -> bool:
        """
        判断是否已配置 OpenAI API Key。

        :return: 已配置时返回 True，否则返回 False。
        """
        return bool(self.openai_api_key)

    @property
    def has_siliconflow_api_key(self) -> bool:
        """
        判断是否已配置 SiliconFlow API Key。

        :return: 已配置时返回 True，否则返回 False。
        """
        return bool(self.siliconflow_api_key)


def _read_env(name: str, default: str | None = None) -> str | None:
    """
    读取并清理单个环境变量。

    :param name: 环境变量名称。
    :param default: 环境变量缺失时使用的默认值。
    :return: 清理后的字符串；没有有效值时返回 None。
    """
    value = os.getenv(name, default)
    if value is None:
        return None

    value = value.strip()
    return value or None


def _read_positive_int(name: str, *, default: int) -> int:
    """
    读取正整数环境变量。

    :param name: 环境变量名称。
    :param default: 环境变量缺失时使用的默认值。
    :return: 解析后的正整数。
    """
    raw_value = _read_env(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value
