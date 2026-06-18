import json

import pytest

from app.core.config import AppSettings
from app.services.llm_provider import (
    DashScopeLLMProvider,
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
            dashscope_model="qwen-plus",
            dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    )

    assert isinstance(provider, FakeLLMProvider)


def test_create_llm_provider_can_build_dashscope_provider():
    provider = create_llm_provider(
        AppSettings(
            llm_provider="dashscope",
            dashscope_api_key="dashscope-test-key",
            openai_api_key=None,
            dashscope_model="qwen-plus",
            dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    )

    assert isinstance(provider, DashScopeLLMProvider)
    assert provider.name == "dashscope"
    assert provider.model == "qwen-plus"


def test_create_llm_provider_requires_dashscope_key_when_selected():
    with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
        create_llm_provider(
            AppSettings(
                llm_provider="dashscope",
                dashscope_api_key=None,
                openai_api_key=None,
                dashscope_model="qwen-plus",
                dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        )


def test_dashscope_provider_posts_openai_compatible_request(monkeypatch):
    captured: dict[str, object] = {}

    class FakeHTTPResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "model": "qwen-plus",
                    "choices": [
                        {
                            "message": {
                                "content": "你好，我是千问。"
                            }
                        }
                    ],
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["authorization"] = request.get_header("Authorization")
        captured["content_type"] = request.get_header("Content-type")
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeHTTPResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = DashScopeLLMProvider(
        api_key="dashscope-test-key",
        model="qwen-plus",
        base_url="https://dashscope.example/compatible-mode/v1",
    )
    completion = provider.complete("请用一句话解释这个训练计划")

    assert captured["url"] == "https://dashscope.example/compatible-mode/v1/chat/completions"
    assert captured["method"] == "POST"
    assert captured["authorization"] == "Bearer dashscope-test-key"
    assert captured["content_type"] == "application/json"
    assert captured["timeout"] == 30
    assert captured["body"] == {
        "model": "qwen-plus",
        "messages": [
            {
                "role": "system",
                "content": "你是 FitFlow AI 的健身教练，只能解释已经通过安全规则的训练计划。",
            },
            {
                "role": "user",
                "content": "请用一句话解释这个训练计划",
            },
        ],
        "temperature": 0.2,
    }
    assert completion.provider == "dashscope"
    assert completion.model == "qwen-plus"
    assert completion.content == "你好，我是千问。"
