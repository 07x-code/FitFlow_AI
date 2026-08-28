from uuid import uuid4
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """
    创建已启动应用生命周期的测试客户端。

    :return: 可用于调用 Proposal API 的测试客户端。
    """
    with TestClient(app) as test_client:
        yield test_client


def unique_user_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def save_profile(
    client: TestClient,
    user_id: str,
    *,
    health_flags: list[str] | None = None,
) -> None:
    response = client.post(
        "/api/profiles",
        headers={"X-User-ID": user_id},
        json={
            "age": 22,
            "sex": "male",
            "height_cm": 175,
            "weight_kg": 70,
            "goal": "muscle_gain",
            "sessions_per_week": 3,
            "session_minutes": 60,
            "health_flags": health_flags or [],
        },
    )
    assert response.status_code == 201


def create_proposal(client: TestClient, user_id: str) -> dict:
    response = client.post(
        "/api/proposals/training-plan",
        headers={"X-User-ID": user_id},
    )
    assert response.status_code == 201
    return response.json()


def get_history(client: TestClient, user_id: str) -> dict:
    response = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": user_id},
    )
    assert response.status_code == 200
    return response.json()


def test_create_training_plan_proposal_does_not_save_history(client: TestClient):
    """
    验证初始训练计划 Proposal 包含目标周和修订元数据。

    :return: 无返回值。
    """
    user_id = unique_user_id("proposal-user")
    save_profile(client, user_id)

    body = create_proposal(client, user_id)
    proposals_response = client.get(
        "/api/proposals",
        headers={"X-User-ID": user_id},
    )

    assert body["type"] == "training_plan"
    assert body["operation"] == "create"
    assert body["target_week_start"] == body["plan"]["week_start"]
    assert body["base_plan_id"] is None
    assert body["parent_proposal_id"] is None
    assert body["revision"] == 1
    assert body["generation_summary"] == body["plan"]["goal_summary"]
    assert body["status"] == "pending"
    assert body["approved_plan_id"] is None
    assert body["decision_note"] is None
    assert body["decided_at"] is None
    assert len(body["plan"]["days"]) == 3
    assert body["safety_check"] == {"valid": True, "violations": []}
    assert get_history(client, user_id) == {"plans": []}
    assert proposals_response.status_code == 200
    assert proposals_response.json()["proposals"][0]["id"] == body["id"]


def test_approve_training_plan_proposal_saves_plan_to_history(client: TestClient):
    user_id = unique_user_id("approve-proposal-user")
    save_profile(client, user_id)
    proposal = create_proposal(client, user_id)

    response = client.post(
        f"/api/proposals/{proposal['id']}/decision",
        headers={"X-User-ID": user_id},
        json={
            "decision": "approve",
            "decision_note": "This plan looks safe.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["decision_note"] == "This plan looks safe."
    assert body["approved_plan_id"] is not None
    assert body["decided_at"] is not None
    history = get_history(client, user_id)
    assert len(history["plans"]) == 1
    assert history["plans"][0]["id"] == body["approved_plan_id"]
    assert history["plans"][0]["plan"] == proposal["plan"]


def test_reject_training_plan_proposal_does_not_save_history(client: TestClient):
    user_id = unique_user_id("reject-proposal-user")
    save_profile(client, user_id)
    proposal = create_proposal(client, user_id)

    response = client.post(
        f"/api/proposals/{proposal['id']}/decision",
        headers={"X-User-ID": user_id},
        json={
            "decision": "reject",
            "decision_note": "I want fewer lower body exercises.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["decision_note"] == "I want fewer lower body exercises."
    assert body["approved_plan_id"] is None
    assert body["decided_at"] is not None
    assert get_history(client, user_id) == {"plans": []}


def test_training_plan_proposal_blocks_risky_profile(client: TestClient):
    user_id = unique_user_id("risky-proposal-user")
    save_profile(client, user_id, health_flags=["acute_injury"])

    response = client.post(
        "/api/proposals/training-plan",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "message": "Automatic plan generation is blocked.",
        "risk": {
            "level": "blocked",
            "can_auto_plan": False,
        },
    }
    assert get_history(client, user_id) == {"plans": []}


def test_proposal_decision_hides_other_users_proposal(client: TestClient):
    owner_user_id = unique_user_id("proposal-owner")
    other_user_id = unique_user_id("proposal-other")
    save_profile(client, owner_user_id)
    save_profile(client, other_user_id)
    proposal = create_proposal(client, owner_user_id)

    response = client.post(
        f"/api/proposals/{proposal['id']}/decision",
        headers={"X-User-ID": other_user_id},
        json={"decision": "approve"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Proposal not found."
    assert get_history(client, owner_user_id) == {"plans": []}
    assert get_history(client, other_user_id) == {"plans": []}


def test_proposal_decision_rejects_already_decided_proposal(client: TestClient):
    user_id = unique_user_id("double-decision-proposal-user")
    save_profile(client, user_id)
    proposal = create_proposal(client, user_id)

    first_response = client.post(
        f"/api/proposals/{proposal['id']}/decision",
        headers={"X-User-ID": user_id},
        json={"decision": "approve"},
    )
    second_response = client.post(
        f"/api/proposals/{proposal['id']}/decision",
        headers={"X-User-ID": user_id},
        json={"decision": "reject", "decision_note": "Changed my mind."},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Proposal has already been decided."
    history = get_history(client, user_id)
    assert len(history["plans"]) == 1
