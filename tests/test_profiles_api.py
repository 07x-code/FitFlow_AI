from importlib import reload

from fastapi.testclient import TestClient

from app.api import profiles as profiles_api
from app.main import app


def test_create_profile_returns_risk_and_nutrition_assessment():
    response = TestClient(app).post(
        "/api/profiles",
        headers={"X-User-ID": "demo-user"},
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


def test_create_profile_declares_response_model_in_openapi():
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    response_schema = schema["paths"]["/api/profiles"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"]

    assert response_schema == {"$ref": "#/components/schemas/ProfileAssessmentResponse"}


def test_get_profile_returns_saved_profile_for_user():
    client = TestClient(app)
    client.post(
        "/api/profiles",
        headers={"X-User-ID": "saved-user"},
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

    response = client.get("/api/profiles/me", headers={"X-User-ID": "saved-user"})

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["goal"] == "muscle_gain"
    assert body["nutrition"]["protein_target_g"] == 112


def test_get_profile_survives_profiles_module_reload():
    client = TestClient(app)
    client.post(
        "/api/profiles",
        headers={"X-User-ID": "sqlite-user"},
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

    reload(profiles_api)   #重新加载模块，验证SQLite
    response = client.get("/api/profiles/me", headers={"X-User-ID": "sqlite-user"})

    assert response.status_code == 200
    assert response.json()["profile"]["goal"] == "muscle_gain"
