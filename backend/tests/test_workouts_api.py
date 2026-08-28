from uuid import uuid4
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """
    创建已启动应用生命周期的测试客户端。

    :return: 可用于调用 Workout API 的测试客户端。
    """
    with TestClient(app) as test_client:
        yield test_client


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


def create_plan_and_get_id(
    client: TestClient,
    user_id: str,
) -> int:
    """
    创建并批准 Proposal，返回生成的正式计划标识。

    :param client: 已启动应用生命周期的测试客户端。
    :param user_id: 用户标识。
    :return: 批准 Proposal 后生成的正式计划标识。
    """
    proposal_response = client.post(
        "/api/proposals/training-plan",
        headers={"X-User-ID": user_id},
    )
    assert proposal_response.status_code == 201

    proposal_id = proposal_response.json()["id"]
    decision_response = client.post(
        f"/api/proposals/{proposal_id}/decision",
        headers={"X-User-ID": user_id},
        json={"decision": "approve"},
    )
    assert decision_response.status_code == 200

    approved_plan_id = decision_response.json()["approved_plan_id"]
    assert approved_plan_id is not None

    return approved_plan_id

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


def test_submit_workout_session_records_training_feedback(client: TestClient):
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


def test_submit_workout_session_returns_safety_alert_for_high_pain_or_fatigue(client: TestClient):
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


def test_submit_workout_session_hides_other_users_plan(client: TestClient):
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


def test_submit_workout_session_links_to_selected_plan_day(client: TestClient):
    user_id = unique_user_id("workout-day-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)
    payload = workout_payload()
    payload["plan_day_index"] = 2
    payload["sets"][0]["exercise_id"] = "exercise-0001"
    payload["sets"][0]["exercise_name"] = "Leg Press"

    response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": user_id},
        json=payload,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["plan_day_index"] == 2
    assert body["plan_day_name"] == "Day 2 - Full Body B"
    assert body["sets"][0]["exercise_id"] == "exercise-0001"


def test_submit_workout_session_rejects_unknown_plan_day(client: TestClient):
    user_id = unique_user_id("unknown-workout-day-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)
    payload = workout_payload()
    payload["plan_day_index"] = 4

    response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": user_id},
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Plan day 4 does not exist. This plan has 3 days."
    )


def test_submit_workout_session_rejects_exercise_outside_selected_day(client: TestClient):
    user_id = unique_user_id("unplanned-exercise-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)
    payload = workout_payload()
    payload["sets"][0]["exercise_name"] = "Leg Press"

    response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": user_id},
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "message": "Workout contains exercises outside the selected plan day.",
        "unplanned_exercises": ["Leg Press"],
    }


def test_workout_history_can_be_filtered_by_plan(
    client: TestClient,
) -> None:
    """
    验证训练记录历史支持按正式计划标识筛选。

    :param client: 已启动应用生命周期的测试客户端。
    :return: 无返回值。
    """
    user_id = unique_user_id("filtered-workout-history-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)

    saved_response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": user_id},
        json=workout_payload(),
    )
    matching_response = client.get(
        f"/api/workouts/history?plan_id={plan_id}",
        headers={"X-User-ID": user_id},
    )
    missing_response = client.get(
        f"/api/workouts/history?plan_id={plan_id + 9999}",
        headers={"X-User-ID": user_id},
    )

    assert saved_response.status_code == 201
    assert matching_response.status_code == 200
    assert [
        session["plan_id"]
        for session in matching_response.json()["sessions"]
    ] == [plan_id]
    assert missing_response.status_code == 200
    assert missing_response.json() == {"sessions": []}