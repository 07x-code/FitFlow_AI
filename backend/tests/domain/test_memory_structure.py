from pathlib import Path

from app.domain.models.user_memory import UserMemoryCreate
from app.domain.models.working_memory import (
    ConversationRole,
    WorkingMemoryItem,
    WorkingMemoryKind,
)
from app.domain.policies.working_memory import trim_working_memory


APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_memory_models_and_policies_use_consistent_directories() -> None:
    """
    验证记忆模型和策略使用统一的类型优先目录结构。

    :return: 无返回值。
    """
    assert not (APP_ROOT / "domain" / "memory").exists()
    assert (APP_ROOT / "domain" / "models" / "user_memory.py").is_file()
    assert (APP_ROOT / "domain" / "models" / "working_memory.py").is_file()
    assert (APP_ROOT / "domain" / "policies" / "working_memory.py").is_file()


def test_memory_model_and_policy_imports_are_available() -> None:
    """
    验证长期记忆、工作记忆和淘汰策略可以从新路径使用。

    :return: 无返回值。
    """
    user_memory = UserMemoryCreate(
        type="preferred_equipment",
        content="偏好哑铃训练。",
    )
    working_memory = WorkingMemoryItem(
        kind=WorkingMemoryKind.MESSAGE,
        role=ConversationRole.USER,
        content="今天练什么？",
    )

    assert user_memory.content == "偏好哑铃训练。"
    assert trim_working_memory([working_memory], capacity=1) == [
        working_memory
    ]
