from fastapi.testclient import TestClient

from app.main import app


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
    save_profile(client, "training-plan-user")

    response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": "training-plan-user"},
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
    response = TestClient(app).post(
        "/api/training-plans/draft",
        headers={"X-User-ID": "missing-training-plan-user"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found."


def test_create_training_plan_draft_blocks_risky_profile():
    client = TestClient(app)
    save_profile(client, "risky-training-plan-user", health_flags=["chest_pain"])

    response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": "risky-training-plan-user"},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["risk"] == {
        "level": "blocked",
        "can_auto_plan": False,
    }
