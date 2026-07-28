from collections.abc import MutableMapping
from typing import Any


STEPS = (
    "1. 用户画像",
    "2. 计划草案",
    "3. 人工确认",
    "4. 训练打卡",
    "5. 周报调整",
    "6. AI 教练",
)

DEFAULT_STATE = {
    "api_base_url": "http://127.0.0.1:8000",
    "user_id": "demo-user",
    "current_step": STEPS[0],
    "risk_level": None,
    "profile_result": None,
    "proposal_id": None,
    "proposal_result": None,
    "approved_plan_id": None,
    "decision_result": None,
    "workout_result": None,
    "weekly_report": None,
    "weekly_adjustment_proposal_id": None,
    "chat_messages": [],
}


def ensure_demo_state(state: MutableMapping[str, Any]) -> None:
    for key, value in DEFAULT_STATE.items():
        if key not in state:
            state[key] = value.copy() if isinstance(value, list) else value


def set_current_step(
    state: MutableMapping[str, Any],
    step: str,
) -> None:
    if step not in STEPS:
        raise ValueError(f"Unknown demo step: {step}")
    state["current_step"] = step


def save_profile_result(
    state: MutableMapping[str, Any],
    result: dict[str, Any],
) -> None:
    state["profile_result"] = result
    state["risk_level"] = result["risk"]["level"]


def save_proposal(
    state: MutableMapping[str, Any],
    result: dict[str, Any],
) -> None:
    state["proposal_result"] = result
    state["proposal_id"] = result["id"]


def save_decision(
    state: MutableMapping[str, Any],
    result: dict[str, Any],
) -> None:
    state["decision_result"] = result
    state["proposal_id"] = result["id"]
    if result["status"] == "approved":
        state["approved_plan_id"] = result["approved_plan_id"]


def save_workout_result(
    state: MutableMapping[str, Any],
    result: dict[str, Any],
) -> None:
    state["workout_result"] = result


def save_weekly_report(
    state: MutableMapping[str, Any],
    result: dict[str, Any],
) -> None:
    state["weekly_report"] = result
    proposal = result.get("adjustment_proposal")
    state["weekly_adjustment_proposal_id"] = (
        proposal["id"] if proposal is not None else None
    )


def append_chat_message(
    state: MutableMapping[str, Any],
    *,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    state["chat_messages"].append(
        {
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
    )
