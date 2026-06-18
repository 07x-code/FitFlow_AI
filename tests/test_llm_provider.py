import pytest

from app.core.config import AppSettings
from app.services.llm_provider import (
    DryRunLLMProvider,
    FakeLLMProvider,
    create_llm_provider,
)


def test_fake_llm_provider_returns_deterministic_offline_completion():
    completion = FakeLLMProvider().complete("解释这个训练计划")

    assert completion.provider == "fake"
    assert completion.model == "offline-placeholder"
    assert "离线模拟回复" in completion.content


def test_create_llm_provider_uses_fake_provider_by_default():
    provider = create_llm_provider(
        AppSettings(
            llm_provider="fake",
            dashscope_api_key=None,
            openai_api_key=None,
        )
    )

    assert isinstance(provider, FakeLLMProvider)


def test_create_llm_provider_can_build_dashscope_dry_run_provider():
    provider = create_llm_provider(
        AppSettings(
            llm_provider="dashscope",
            dashscope_api_key="dashscope-test-key",
            openai_api_key=None,
        )
    )

    assert isinstance(provider, DryRunLLMProvider)
    assert provider.name == "dashscope"
    assert provider.complete("hello").provider == "dashscope"


def test_create_llm_provider_requires_dashscope_key_when_selected():
    with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
        create_llm_provider(
            AppSettings(
                llm_provider="dashscope",
                dashscope_api_key=None,
                openai_api_key=None,
            )
        )
