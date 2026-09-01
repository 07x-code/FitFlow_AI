import re

from app.domain.models.user_memory import (
    MemoryCandidate,
    MemoryCommand,
    MemoryCommandAction,
    MemoryType,
)


TEMPORARY_MARKERS = (
    "今天",
    "今晚",
    "明天",
    "这次",
    "本次",
    "这周",
    "本周",
    "下周",
)
PERSISTENT_MARKERS = (
    "以后",
    "今后",
    "一直",
    "通常",
    "平时",
    "长期",
    "每周",
    "总是",
    "习惯",
    "固定",
    "记住",
)
EQUIPMENT_WORDS = (
    "哑铃",
    "杠铃",
    "弹力带",
    "壶铃",
    "固定器械",
    "史密斯机",
    "拉力器",
    "龙门架",
    "徒手",
    "健身房",
    "在家",
    "家里",
)
BODY_WORDS = (
    "左肩",
    "右肩",
    "肩",
    "左膝",
    "右膝",
    "膝盖",
    "膝",
    "腰",
    "下背",
    "背",
    "手腕",
    "肘",
    "脚踝",
    "髋",
    "颈",
)
MINIMUM_MODEL_CONFIDENCE = 0.8
UNCERTAIN_MARKERS = (
    "是不是",
    "是否",
    "可能",
    "怀疑",
    "感觉像",
    "会不会",
)


def validate_memory_candidates(
    message: str,
    candidates: list[MemoryCandidate],
) -> list[MemoryCommand]:
    """
    将大模型候选转换为通过安全校验的长期记忆命令。

    候选必须来自用户原文、属于稳定信息且具有足够置信度。程序仅使用
    用户原文生成记忆内容，避免把体态描述推断为疾病诊断。

    :param message: 当前用户发送的原始消息。
    :param candidates: 大模型返回的结构化记忆候选。
    :return: 已通过安全校验并去重的长期记忆命令。
    """
    commands: list[MemoryCommand] = []
    for candidate in candidates:
        command = _validate_candidate(message, candidate)
        if command is not None:
            commands.append(command)

    unique: dict[tuple[MemoryType, str], MemoryCommand] = {}
    for command in commands:
        unique[(command.type, command.memory_key)] = command
    return list(unique.values())


def extract_memory_commands(message: str) -> list[MemoryCommand]:
    """
    从用户消息中提取明确的长期训练记忆命令。

    :param message: 当前用户发送的原始消息。
    :return: 已通过稳定性规则筛选并去重的记忆命令。
    """
    commands: list[MemoryCommand] = []
    for sentence in _sentences(message):
        command = _extract_sentence(sentence)
        if command is not None:
            commands.append(command)

    unique: dict[tuple[MemoryType, str], MemoryCommand] = {}
    for command in commands:
        unique[(command.type, command.memory_key)] = command
    return list(unique.values())


def _validate_candidate(
    message: str,
    candidate: MemoryCandidate,
) -> MemoryCommand | None:
    """
    校验单条大模型候选并生成规范化记忆命令。

    :param message: 当前用户发送的原始消息。
    :param candidate: 待校验的大模型记忆候选。
    :return: 通过校验的记忆命令；候选不安全时返回 None。
    """
    evidence = candidate.evidence.strip().strip("，,。！？!?；;")
    value = candidate.value.strip().strip("，,。！？!?；;")
    if not candidate.is_explicit or candidate.is_temporary:
        return None
    if candidate.confidence < MINIMUM_MODEL_CONFIDENCE:
        return None
    if not evidence or evidence not in message:
        return None
    if not value or value not in evidence:
        return None
    if _is_temporary(evidence):
        return None
    if any(marker in evidence for marker in UNCERTAIN_MARKERS):
        return None

    memory_key = _candidate_memory_key(candidate.type, value)
    if memory_key is None:
        return None
    return MemoryCommand(
        action=candidate.action,
        type=candidate.type,
        memory_key=memory_key,
        content=_candidate_content(candidate, evidence, value),
    )


def _candidate_memory_key(
    memory_type: MemoryType,
    value: str,
) -> str | None:
    """
    根据候选类型和值生成稳定的记忆键。

    :param memory_type: 长期记忆类型。
    :param value: 用户原文中的核心记忆值。
    :return: 规范化记忆键；不允许自动写入的类型返回 None。
    """
    key_part = _key_part(value)[:120]
    if not key_part:
        return None
    if memory_type is MemoryType.DISLIKED_EXERCISE:
        return f"exercise:{key_part}"
    if memory_type is MemoryType.PREFERRED_EQUIPMENT:
        return "equipment:default"
    if memory_type is MemoryType.TRAINING_TIME:
        return "schedule:weekly"
    if memory_type is MemoryType.PHYSICAL_LIMITATION:
        return f"limitation:{key_part}"
    return None


def _candidate_content(
    candidate: MemoryCandidate,
    evidence: str,
    value: str,
) -> str:
    """
    使用用户原文生成长期记忆展示内容。

    :param candidate: 已通过基础安全校验的大模型候选。
    :param evidence: 用户消息中的原文证据。
    :param value: 用户原文中的核心记忆值。
    :return: 可写入数据库的长期记忆内容。
    """
    if candidate.action is MemoryCommandAction.FORGET:
        if candidate.type is MemoryType.DISLIKED_EXERCISE:
            return f"已不再排除{value}。"
        return f"已取消：{_display_sentence(evidence)}"
    if candidate.type is MemoryType.DISLIKED_EXERCISE:
        return f"以后不安排{value}。"
    if candidate.type is MemoryType.PHYSICAL_LIMITATION:
        return f"用户自述：{_display_sentence(evidence)}"
    return _display_sentence(evidence)


def _extract_sentence(sentence: str) -> MemoryCommand | None:
    """
    从单个用户分句中提取一条长期记忆命令。

    :param sentence: 已去除外围标点的用户分句。
    :return: 匹配到的记忆命令；当前分句不应持久化时返回 None。
    """
    forgotten = _extract_forgotten_exercise(sentence)
    if forgotten is not None:
        return forgotten

    if _is_temporary(sentence):
        return None

    limitation = _extract_physical_limitation(sentence)
    if limitation is not None:
        return limitation

    disliked = _extract_disliked_exercise(sentence)
    if disliked is not None:
        return disliked

    equipment = _extract_equipment(sentence)
    if equipment is not None:
        return equipment

    return _extract_training_time(sentence)


def _extract_forgotten_exercise(sentence: str) -> MemoryCommand | None:
    patterns = (
        r"^(?:请)?(?:忘掉|删除|取消).*?(?:不喜欢|排除|不安排)(?P<item>.+)",
        r"^(?:我)?(?:现在|已经)?(?:可以|能)(?:重新)?做(?P<item>.+)",
        r"^(?:我)?(?:现在|已经)喜欢(?P<item>.+)",
    )
    for pattern in patterns:
        match = re.search(pattern, sentence)
        if match is None:
            continue
        item = _clean_item(match.group("item"))
        if not item or item.startswith("用"):
            continue
        return MemoryCommand(
            action=MemoryCommandAction.FORGET,
            type=MemoryType.DISLIKED_EXERCISE,
            memory_key=f"exercise:{_key_part(item)}",
            content=f"已不再排除{item}。",
        )
    return None


def _extract_disliked_exercise(sentence: str) -> MemoryCommand | None:
    patterns = (
        r"(?:我)?(?:很|非常)?(?:不喜欢|讨厌)(?P<item>.+)",
        r"(?:以后|今后)?(?:不要|别)(?:再)?(?:给我)?安排(?P<item>.+)",
    )
    for pattern in patterns:
        match = re.search(pattern, sentence)
        if match is None:
            continue
        item = _clean_item(match.group("item"))
        if not item:
            continue
        return MemoryCommand(
            action=MemoryCommandAction.REMEMBER,
            type=MemoryType.DISLIKED_EXERCISE,
            memory_key=f"exercise:{_key_part(item)}",
            content=f"以后不安排{item}。",
        )
    return None


def _extract_equipment(sentence: str) -> MemoryCommand | None:
    if not any(word in sentence for word in EQUIPMENT_WORDS):
        return None
    cues = ("只有", "偏好", "喜欢用", "常用", "主要用", "可以使用", "器械")
    if not any(cue in sentence for cue in cues):
        return None
    return MemoryCommand(
        action=MemoryCommandAction.REMEMBER,
        type=MemoryType.PREFERRED_EQUIPMENT,
        memory_key="equipment:default",
        content=_display_sentence(sentence),
    )


def _extract_training_time(sentence: str) -> MemoryCommand | None:
    if "训练" not in sentence and "锻炼" not in sentence:
        return None
    if not any(marker in sentence for marker in PERSISTENT_MARKERS):
        return None
    time_words = ("周", "星期", "早上", "上午", "中午", "下午", "晚上", "夜间")
    if not any(word in sentence for word in time_words):
        return None
    return MemoryCommand(
        action=MemoryCommandAction.REMEMBER,
        type=MemoryType.TRAINING_TIME,
        memory_key="schedule:weekly",
        content=_display_sentence(sentence),
    )


def _extract_physical_limitation(sentence: str) -> MemoryCommand | None:
    pain_cues = ("会疼", "会痛", "一直疼", "一直痛", "经常疼", "经常痛", "不适", "不能做")
    if not any(cue in sentence for cue in pain_cues):
        return None
    if not any(word in sentence for word in BODY_WORDS) and "不能做" not in sentence:
        return None
    return MemoryCommand(
        action=MemoryCommandAction.REMEMBER,
        type=MemoryType.PHYSICAL_LIMITATION,
        memory_key=f"limitation:{_key_part(sentence)[:120]}",
        content=f"用户报告：{_display_sentence(sentence)}",
    )


def _is_temporary(sentence: str) -> bool:
    return (
        any(marker in sentence for marker in TEMPORARY_MARKERS)
        and not any(marker in sentence for marker in PERSISTENT_MARKERS)
    )


def _sentences(message: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"[，,。！？!?；;\n]+", message.strip())
        if part.strip()
    ]


def _clean_item(value: str) -> str:
    item = re.split(r"(?:以后|今后|因为|这条记忆)", value, maxsplit=1)[0]
    item = re.sub(r"^(?:这个|这项|做)", "", item.strip())
    item = re.sub(r"(?:这个动作|这项动作|动作|了|吧)$", "", item.strip())
    return item.strip(" ：:、")[:80]


def _key_part(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", value).casefold()


def _display_sentence(sentence: str) -> str:
    return f"{sentence.rstrip('。')}。"
