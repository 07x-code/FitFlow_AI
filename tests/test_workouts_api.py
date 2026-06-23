from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def unique_user_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def save_profile(client: TestClient, user_id: str) -> None:
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
            "health_flags": [],
        },
    )
    assert response.status_code == 201


def create_plan_and_get_id(client: TestClient, user_id: str) -> int:
    response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    assert response.status_code == 201

    history_response = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": user_id},
    )
    assert history_response.status_code == 200
    return history_response.json()["plans"][0]["id"]


def workout_payload(*, fatigue_level: int = 5, pain_level: int = 0) -> dict:
    return {
        "completed": True,
        "fatigue_level": fatigue_level,
        "pain_level": pain_level,
        "notes": "Felt stable overall.",
        "sets": [
            {
                "exercise_name": "Goblet Squat",
                "set_number": 1,
                "weight_kg": 20,
                "reps": 10,
                "rpe": 7,
            }
        ],
    }


def test_submit_workout_session_records_training_feedback():
    client = TestClient(app)
    user_id = unique_user_id("workout-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)

    response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": user_id},
        json=workout_payload(),
    )
    history_response = client.get(
        "/api/workouts/history",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["plan_id"] == plan_id
    assert body["completed"] is True
    assert body["fatigue_level"] == 5
    assert body["pain_level"] == 0
    assert body["safety_alert"] is None
    assert body["sets"][0]["exercise_name"] == "Goblet Squat"
    assert "created_at" in body
    assert history_response.status_code == 200
    assert history_response.json()["sessions"][0]["id"] == body["id"]


def test_submit_workout_session_returns_safety_alert_for_high_pain_or_fatigue():
    client = TestClient(app)
    user_id = unique_user_id("alert-workout-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)

    response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": user_id},
        json=workout_payload(fatigue_level=9, pain_level=7),
    )

    assert response.status_code == 201
    assert response.json()["safety_alert"] == {
        "level": "caution",
        "message": (
            "本次反馈显示疼痛或疲劳偏高，请暂停加量，必要时停止训练并咨询专业人士。"
        ),
    }


def test_submit_workout_session_hides_other_users_plan():
    client = TestClient(app)
    owner_user_id = unique_user_id("workout-owner")
    other_user_id = unique_user_id("workout-other")
    save_profile(client, owner_user_id)
    save_profile(client, other_user_id)
    plan_id = create_plan_and_get_id(client, owner_user_id)

    response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": other_user_id},
        json=workout_payload(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Training plan not found."
