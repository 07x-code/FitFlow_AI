from app.domain.models import (
    MemoryCandidate,
    MemoryCommandAction,
    MemoryType,
)
from app.domain.policies.long_term_memory import (
    extract_memory_commands,
    validate_memory_candidates,
)


def test_explicit_disliked_exercise_becomes_long_term_memory() -> None:
    """
    验证明确的长期动作偏好会转换为排除动作记忆。

    :return: 无返回值。
    """
    commands = extract_memory_commands("我不喜欢飞鸟，以后别安排。")

    assert len(commands) == 1
    assert commands[0].action is MemoryCommandAction.REMEMBER
    assert commands[0].type is MemoryType.DISLIKED_EXERCISE
    assert commands[0].memory_key == "exercise:飞鸟"
    assert commands[0].content == "以后不安排飞鸟。"


def test_temporary_preference_stays_out_of_long_term_memory() -> None:
    """
    验证只约束今天的表达不会生成长期记忆命令。

    :return: 无返回值。
    """
    assert extract_memory_commands("今天不想做飞鸟。") == []


def test_regular_training_time_becomes_long_term_memory() -> None:
    """
    验证规律性的训练时间会转换为长期记忆。

    :return: 无返回值。
    """
    commands = extract_memory_commands("我通常周三晚上训练。")

    assert len(commands) == 1
    assert commands[0].type is MemoryType.TRAINING_TIME
    assert commands[0].memory_key == "schedule:weekly"


def test_preferred_equipment_is_not_treated_as_exercise_recovery() -> None:
    """
    验证器械偏好会写入器械类型而不是误删动作偏好。

    :return: 无返回值。
    """
    commands = extract_memory_commands("我喜欢用哑铃训练。")

    assert len(commands) == 1
    assert commands[0].action is MemoryCommandAction.REMEMBER
    assert commands[0].type is MemoryType.PREFERRED_EQUIPMENT


def test_user_can_forget_disliked_exercise() -> None:
    """
    验证用户明确恢复动作时会生成忘记命令。

    :return: 无返回值。
    """
    commands = extract_memory_commands("我现在喜欢飞鸟了。")

    assert len(commands) == 1
    assert commands[0].action is MemoryCommandAction.FORGET
    assert commands[0].memory_key == "exercise:飞鸟"


def test_user_reported_recurring_pain_becomes_limitation() -> None:
    """
    验证用户报告的重复疼痛会保存为身体限制而非疾病诊断。

    :return: 无返回值。
    """
    commands = extract_memory_commands("我做推举时右肩会疼。")

    assert len(commands) == 1
    assert commands[0].type is MemoryType.PHYSICAL_LIMITATION
    assert commands[0].content == "用户报告：我做推举时右肩会疼。"
    assert "损伤" not in commands[0].content


def test_model_candidate_preserves_reported_physical_condition() -> None:
    """
    验证身体情况候选按用户原文保存，不转换为医学诊断。

    :return: 无返回值。
    """
    message = "我有肱骨前移"
    candidates = [
        MemoryCandidate(
            action=MemoryCommandAction.REMEMBER,
            type=MemoryType.PHYSICAL_LIMITATION,
            value="肱骨前移",
            evidence=message,
            confidence=0.96,
            is_explicit=True,
            is_temporary=False,
        )
    ]

    commands = validate_memory_candidates(message, candidates)

    assert len(commands) == 1
    assert commands[0].memory_key == "limitation:肱骨前移"
    assert commands[0].content == "用户自述：我有肱骨前移。"
    assert "撞击" not in commands[0].content


def test_model_candidate_without_verbatim_evidence_is_rejected() -> None:
    """
    验证模型推断出的非原文身体诊断不会进入长期记忆。

    :return: 无返回值。
    """
    candidates = [
        MemoryCandidate(
            action=MemoryCommandAction.REMEMBER,
            type=MemoryType.PHYSICAL_LIMITATION,
            value="肩峰撞击综合征",
            evidence="我有肩峰撞击综合征",
            confidence=0.99,
            is_explicit=True,
            is_temporary=False,
        )
    ]

    assert validate_memory_candidates("我有肱骨前移", candidates) == []


def test_uncertain_model_candidate_is_rejected() -> None:
    """
    验证用户提问或猜测不会被模型候选固化为长期事实。

    :return: 无返回值。
    """
    message = "我是不是有肱骨前移"
    candidates = [
        MemoryCandidate(
            action=MemoryCommandAction.REMEMBER,
            type=MemoryType.PHYSICAL_LIMITATION,
            value="肱骨前移",
            evidence=message,
            confidence=0.92,
            is_explicit=True,
            is_temporary=False,
        )
    ]

    assert validate_memory_candidates(message, candidates) == []
