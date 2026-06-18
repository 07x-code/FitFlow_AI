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


def test_settings_uses_dashscope_defaults(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_MODEL", raising=False)
    monkeypatch.delenv("DASHSCOPE_BASE_URL", raising=False)

    settings = AppSettings.from_env()

    assert settings.dashscope_model == "qwen-plus"
    assert settings.dashscope_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
