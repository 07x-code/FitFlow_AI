import pytest

from app.core.config import AppSettings
from app.infrastructure.memory.factory import create_working_memory_store
from app.infrastructure.memory.in_memory import InMemoryWorkingMemoryStore


def test_settings_reads_working_memory_environment(monkeypatch):
    monkeypatch.setenv("FITFLOW_WORKING_MEMORY_BACKEND", "memory")
    monkeypatch.setenv(
        "FITFLOW_REDIS_URL",
        "redis://localhost:6380/2",
    )
    monkeypatch.setenv("FITFLOW_WORKING_MEMORY_TTL_SECONDS", "60")
    monkeypatch.setenv("FITFLOW_WORKING_MEMORY_CAPACITY", "5")

    settings = AppSettings.from_env()

    assert settings.working_memory_backend == "memory"
    assert settings.redis_url == "redis://localhost:6380/2"
    assert settings.working_memory_ttl_seconds == 60
    assert settings.working_memory_capacity == 5


def test_settings_rejects_invalid_working_memory_integer(monkeypatch):
    monkeypatch.setenv("FITFLOW_WORKING_MEMORY_CAPACITY", "0")

    with pytest.raises(ValueError, match="positive integer"):
        AppSettings.from_env()


def test_factory_builds_configured_in_memory_store():
    settings = AppSettings(
        llm_provider="fake",
        dashscope_api_key=None,
        openai_api_key=None,
        dashscope_model="qwen-plus",
        dashscope_base_url="https://example.com",
        working_memory_backend="memory",
        working_memory_ttl_seconds=90,
        working_memory_capacity=7,
    )

    store = create_working_memory_store(settings)

    assert isinstance(store, InMemoryWorkingMemoryStore)
    assert store.ttl_seconds == 90
    assert store.capacity == 7
