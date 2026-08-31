import pytest
from app.core.config import AppSettings


def test_settings_reads_llm_environment_variables(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dashscope-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("DASHSCOPE_MODEL", "qwen-turbo")
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://example.com/compatible-mode/v1")
    monkeypatch.delenv("FITFLOW_LLM_PROVIDER", raising=False)

    settings = AppSettings.from_env()

    assert settings.llm_provider == "fake"
    assert settings.dashscope_api_key == "dashscope-test-key"
    assert settings.openai_api_key == "openai-test-key"
    assert settings.dashscope_model == "qwen-turbo"
    assert settings.dashscope_base_url == "https://example.com/compatible-mode/v1"
    assert settings.has_dashscope_api_key is True
    assert settings.has_openai_api_key is True


def test_settings_reads_selected_llm_provider(monkeypatch):
    monkeypatch.setenv("FITFLOW_LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dashscope-test-key")

    settings = AppSettings.from_env()

    assert settings.llm_provider == "dashscope"


def test_settings_reads_siliconflow_environment_variables(monkeypatch):
    """
    验证应用配置能够读取硅基流动模型参数。

    :param monkeypatch: Pytest 提供的环境变量替换工具。
    :return: 无返回值。
    """
    monkeypatch.setenv("SILICONFLOW_API_KEY", "siliconflow-test-key")
    monkeypatch.setenv("SILICONFLOW_MODEL", "Qwen/Qwen3.5-4B")
    monkeypatch.setenv(
        "SILICONFLOW_BASE_URL",
        "https://siliconflow.example/v1",
    )

    settings = AppSettings.from_env()

    assert settings.siliconflow_api_key == "siliconflow-test-key"
    assert settings.siliconflow_model == "Qwen/Qwen3.5-4B"
    assert settings.siliconflow_base_url == "https://siliconflow.example/v1"
    assert settings.has_siliconflow_api_key is True


def test_settings_uses_dashscope_defaults(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_MODEL", raising=False)
    monkeypatch.delenv("DASHSCOPE_BASE_URL", raising=False)

    settings = AppSettings.from_env()

    assert settings.dashscope_model == "qwen-plus"
    assert settings.dashscope_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"


def test_settings_reads_database_url(monkeypatch):
    """
    验证应用配置能够读取 PostgreSQL 连接地址。

    :param monkeypatch: Pytest 提供的环境变量替换工具。
    :return: 无返回值。
    """
    database_url = (
        "postgresql+asyncpg://fitflow:fitflow@127.0.0.1:5432/fitflow_test"
    )
    monkeypatch.setenv("FITFLOW_DATABASE_URL", database_url)

    settings = AppSettings.from_env()

    assert settings.database_url == database_url


def test_settings_rejects_empty_database_url(monkeypatch):
    """
    验证应用拒绝空白的 PostgreSQL 连接地址。

    :param monkeypatch: Pytest 提供的环境变量替换工具。
    :return: 无返回值。
    """
    monkeypatch.setenv("FITFLOW_DATABASE_URL", "   ")

    with pytest.raises(ValueError, match="FITFLOW_DATABASE_URL"):
        AppSettings.from_env()

def test_settings_reads_test_database_url(monkeypatch):
    """
    验证应用配置能够读取独立的测试数据库地址。

    :param monkeypatch: Pytest 提供的环境变量替换工具。
    :return: 无返回值。
    """
    test_database_url = (
        "postgresql+asyncpg://fitflow:fitflow@127.0.0.1:5432/fitflow_test"
    )
    monkeypatch.setenv(
        "FITFLOW_TEST_DATABASE_URL",
        test_database_url,
    )

    settings = AppSettings.from_env()

    assert settings.test_database_url == test_database_url


def test_settings_rejects_empty_test_database_url(monkeypatch):
    """
    验证应用拒绝空白的测试数据库地址。

    :param monkeypatch: Pytest 提供的环境变量替换工具。
    :return: 无返回值。
    """
    monkeypatch.setenv("FITFLOW_TEST_DATABASE_URL", "   ")

    with pytest.raises(ValueError, match="FITFLOW_TEST_DATABASE_URL"):
        AppSettings.from_env()
