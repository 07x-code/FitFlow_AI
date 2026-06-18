from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


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


def test_create_training_plan_draft_returns_safe_plan_for_saved_profile():
    client = TestClient(app)
    user_id = unique_user_id("training-plan-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["plan"]["days"]) == 3
    assert body["safety_check"] == {
        "valid": True,
        "violations": [],
    }
    assert all(len(day["exercises"]) == 4 for day in body["plan"]["days"])
    assert all(
        exercise["target_rpe"] <= 8
        for day in body["plan"]["days"]
        for exercise in day["exercises"]
    )


def test_create_training_plan_draft_requires_saved_profile():
    user_id = unique_user_id("missing-training-plan-user")
    response = TestClient(app).post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found."


def test_create_training_plan_draft_blocks_risky_profile():
    client = TestClient(app)
    user_id = unique_user_id("risky-training-plan-user")
    save_profile(client, user_id, health_flags=["chest_pain"])

    response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["risk"] == {
        "level": "blocked",
        "can_auto_plan": False,
    }


def test_create_training_plan_draft_saves_each_generated_plan_to_history():
    client = TestClient(app)
    user_id = unique_user_id("history-training-plan-user")
    save_profile(client, user_id)

    first_response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    second_response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    history_response = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": user_id},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert history_response.status_code == 200
    plans = history_response.json()["plans"]
    assert len(plans) == 2
    assert plans[0]["id"] > plans[1]["id"]
    assert plans[0]["plan"]["days"][0]["name"] == "Day 1 - Full Body A"
    assert plans[0]["safety_check"] == {"valid": True, "violations": []}
    assert "created_at" in plans[0]


def test_training_plan_history_isolated_between_users():
    client = TestClient(app)
    first_user_id = unique_user_id("first-history-user")
    second_user_id = unique_user_id("second-history-user")
    save_profile(client, first_user_id)
    save_profile(client, second_user_id)

    client.post("/api/training-plans/draft", headers={"X-User-ID": first_user_id})
    client.post("/api/training-plans/draft", headers={"X-User-ID": second_user_id})
    client.post("/api/training-plans/draft", headers={"X-User-ID": second_user_id})

    first_history = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": first_user_id},
    )
    second_history = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": second_user_id},
    )

    assert first_history.status_code == 200
    assert second_history.status_code == 200
    assert len(first_history.json()["plans"]) == 1
    assert len(second_history.json()["plans"]) == 2


def test_blocked_training_plan_draft_does_not_save_history():
    client = TestClient(app)
    user_id = unique_user_id("blocked-history-user")
    save_profile(client, user_id, health_flags=["acute_injury"])

    draft_response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    history_response = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": user_id},
    )

    assert draft_response.status_code == 409
    assert history_response.status_code == 200
    assert history_response.json() == {"plans": []}
