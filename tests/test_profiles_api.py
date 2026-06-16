from fastapi.testclient import TestClient

from app.main import app


def test_create_profile_returns_risk_and_nutrition_assessment():
    response = TestClient(app).post(
        "/api/profiles",
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
    body = response.json()
    assert body["profile"]["goal"] == "muscle_gain"
    assert body["risk"] == {
        "level": "low",
        "can_auto_plan": True,
    }
    assert body["nutrition"] == {
        "bmr_kcal": 1689,
        "calorie_target_kcal": 2572,
        "protein_target_g": 112,
    }
