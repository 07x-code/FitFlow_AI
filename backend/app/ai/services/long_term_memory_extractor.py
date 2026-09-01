from pydantic import ValidationError

from app.domain.models import MemoryCandidate
from app.ports.llm import (
    LLMMessage,
    LLMProvider,
    LLMToolDefinition,
)


MEMORY_EXTRACTION_TOOL = LLMToolDefinition(
    name="extract_long_term_memory_candidates",
    description=(
        "提取用户明确表达、会影响未来健身建议的稳定信息。"
        "即使没有候选也必须调用，并返回空 candidates。"
    ),
    parameters={
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["remember", "forget"],
                        },
                        "type": {
                            "type": "string",
                            "enum": [
                                "preferred_equipment",
                                "disliked_exercise",
                                "training_time",
                                "physical_limitation",
                            ],
                        },
                        "value": {"type": "string"},
                        "evidence": {"type": "string"},
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "is_explicit": {"type": "boolean"},
                        "is_temporary": {"type": "boolean"},
                    },
                    "required": [
                        "action",
                        "type",
                        "value",
                        "evidence",
                        "confidence",
                        "is_explicit",
                        "is_temporary",
                    ],
                },
            }
        },
        "required": ["candidates"],
    },
    force_call=True,
)


def extract_memory_candidates(
    llm_provider: LLMProvider,
    message: str,
) -> list[MemoryCandidate] | None:
    """
    使用大模型工具调用从用户消息中提取长期记忆候选。

    :param llm_provider: 支持工具调用的大模型服务。
    :param message: 当前用户发送的原始消息。
    :return: 结构化候选列表；模型调用失败或返回无效结构时返回 None。
    """
    messages = [
        LLMMessage(
            role="system",
            content=(
                "你是健身助手的长期记忆提取器。只提取用户本人明确陈述、"
                "会影响未来训练建议的稳定信息。临时状态、问题、猜测、模型"
                "推断不能作为稳定事实。用户明确自述的身体情况可以提取，但"
                "必须保留用户原话，不得翻译、改写或等同为另一种疾病。"
                "evidence 必须逐字摘自用户消息，value 也必须是 evidence "
                "中的连续原文。"
            ),
        ),
        LLMMessage(role="user", content=message),
    ]
    try:
        completion = llm_provider.complete_with_tools(
            messages,
            (MEMORY_EXTRACTION_TOOL,),
        )
    except (RuntimeError, TypeError, ValueError):
        return None

    tool_call = next(
        (
            call
            for call in completion.tool_calls
            if call.name == MEMORY_EXTRACTION_TOOL.name
        ),
        None,
    )
    if tool_call is None:
        return None

    raw_candidates = tool_call.arguments.get("candidates")
    if not isinstance(raw_candidates, list):
        return None
    try:
        return [
            MemoryCandidate.model_validate(candidate)
            for candidate in raw_candidates
        ]
    except ValidationError:
        return None
