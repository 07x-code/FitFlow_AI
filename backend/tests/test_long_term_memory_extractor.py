import asyncio
from unittest.mock import AsyncMock

from app.ai.services.long_term_memory_extractor import (
    MEMORY_EXTRACTION_TOOL,
    extract_memory_candidates,
)
from app.application.use_cases.memories import MemoryUseCases
from app.domain.models import MemoryType, UserMemoryResponse
from app.ports.llm import (
    LLMCompletion,
    LLMMessage,
    LLMToolCall,
    LLMToolCompletion,
    LLMToolDefinition,
)


class PhysicalConditionCandidateLLM:
    """返回固定身体情况候选的测试大模型。"""

    name = "candidate-test"
    model = "candidate-test-model"

    def complete(self, prompt: str) -> LLMCompletion:
        """
        阻止测试误用普通文本补全。

        :param prompt: 普通补全提示词。
        :return: 此测试不会返回普通补全结果。
        """
        raise AssertionError(f"unexpected prompt: {prompt}")

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: tuple[LLMToolDefinition, ...],
    ) -> LLMToolCompletion:
        """
        返回由长期记忆提取工具承载的结构化候选。

        :param messages: 当前模型消息。
        :param tools: 当前允许调用的工具。
        :return: 包含一条身体情况候选的工具调用结果。
        """
        assert messages[-1].content == "我有肱骨前移"
        assert tools == (MEMORY_EXTRACTION_TOOL,)
        return LLMToolCompletion(
            content=None,
            tool_calls=(
                LLMToolCall(
                    id="memory-call-1",
                    name=MEMORY_EXTRACTION_TOOL.name,
                    arguments={
                        "candidates": [
                            {
                                "action": "remember",
                                "type": "physical_limitation",
                                "value": "肱骨前移",
                                "evidence": "我有肱骨前移",
                                "confidence": 0.96,
                                "is_explicit": True,
                                "is_temporary": False,
                            }
                        ]
                    },
                ),
            ),
            provider=self.name,
            model=self.model,
        )


def test_llm_extracts_structured_long_term_memory_candidate() -> None:
    """
    验证大模型通过工具调用返回结构化长期记忆候选。

    :return: 无返回值。
    """
    candidates = extract_memory_candidates(
        PhysicalConditionCandidateLLM(),
        "我有肱骨前移",
    )

    assert candidates is not None
    assert len(candidates) == 1
    assert candidates[0].type is MemoryType.PHYSICAL_LIMITATION
    assert candidates[0].evidence == "我有肱骨前移"


async def _assert_model_candidate_is_saved() -> None:
    """
    验证记忆用例校验模型候选后执行数据库写入。

    :return: 无返回值。
    """
    repository = AsyncMock()
    repository.upsert_by_key.return_value = UserMemoryResponse(
        id=7,
        type=MemoryType.PHYSICAL_LIMITATION,
        content="用户自述：我有肱骨前移。",
        source="user",
        created_at="2026-08-31T12:00:00+08:00",
    )
    use_cases = MemoryUseCases(
        repository,
        llm=PhysicalConditionCandidateLLM(),
    )

    events = await use_cases.capture_explicit(
        "memory-user",
        "我有肱骨前移",
    )

    memory = repository.upsert_by_key.await_args.args[1]
    assert memory.memory_key == "limitation:肱骨前移"
    assert memory.content == "用户自述：我有肱骨前移。"
    assert events[0].action == "remembered"
    assert events[0].memory_id == 7


def test_memory_use_cases_saves_validated_model_candidate() -> None:
    """
    验证模型识别、安全校验和数据库写入形成完整链路。

    :return: 无返回值。
    """
    asyncio.run(_assert_model_candidate_is_saved())
