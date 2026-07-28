from fitflow_ui.demo_state import (
    STEPS,
    append_chat_message,
    ensure_demo_state,
    save_decision,
    save_profile_result,
    save_proposal,
    save_weekly_report,
    set_current_step,
)


def test_ensure_demo_state_sets_beginner_friendly_defaults():
    state = {}

    ensure_demo_state(state)

    assert state["api_base_url"] == "http://127.0.0.1:8000"
    assert state["user_id"] == "demo-user"
    assert state["current_step"] == STEPS[0]
    assert state["proposal_id"] is None
    assert state["approved_plan_id"] is None
    assert state["chat_messages"] == []


def test_existing_state_is_not_overwritten():
    state = {"user_id": "existing-user", "current_step": STEPS[2]}

    ensure_demo_state(state)

    assert state["user_id"] == "existing-user"
    assert state["current_step"] == STEPS[2]


def test_profile_and_proposal_results_update_state():
    state = {}
    ensure_demo_state(state)

    save_profile_result(
        state,
        {"risk": {"level": "low", "can_auto_plan": True}},
    )
    save_proposal(state, {"id": 7, "status": "pending"})

    assert state["risk_level"] == "low"
    assert state["proposal_id"] == 7
    assert state["proposal_result"]["status"] == "pending"


def test_approved_decision_saves_formal_plan_id():
    state = {}
    ensure_demo_state(state)

    save_decision(
        state,
        {
            "id": 7,
            "status": "approved",
            "approved_plan_id": 12,
        },
    )

    assert state["proposal_id"] == 7
    assert state["approved_plan_id"] == 12


def test_weekly_adjustment_and_chat_are_saved():
    state = {}
    ensure_demo_state(state)

    save_weekly_report(
        state,
        {
            "adjustment_proposal": {
                "id": 21,
                "status": "pending",
            }
        },
    )
    append_chat_message(
        state,
        role="assistant",
        content="保持动作稳定。",
        metadata={"knowledge_sources": []},
    )

    assert state["weekly_adjustment_proposal_id"] == 21
    assert state["chat_messages"][0]["role"] == "assistant"


def test_set_current_step_preserves_other_state():
    state = {}
    ensure_demo_state(state)
    state["proposal_id"] = 7

    set_current_step(state, STEPS[4])

    assert state["current_step"] == STEPS[4]
    assert state["proposal_id"] == 7
