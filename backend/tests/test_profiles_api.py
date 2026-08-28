
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app




@pytest.fixture
def client() -> Iterator[TestClient]:
    """
    创建已启动应用生命周期的测试客户端。

    :return: 可用于调用 Profile API 的测试客户端。
    """
    with TestClient(app) as test_client:
        yield test_client

def test_create_profile_returns_risk_and_nutrition_assessment(client: TestClient):
    response = client.post(
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


def test_create_profile_declares_response_model_in_openapi(client: TestClient):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    response_schema = schema["paths"]["/api/profiles"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"]

    assert response_schema == {"$ref": "#/components/schemas/ProfileAssessmentResponse"}


def test_get_profile_returns_saved_profile_for_user(client: TestClient):
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


