from uuid import uuid4
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """
    创建已运行 FastAPI 生命周期的测试客户端。

    :return: 已连接测试数据库的客户端。
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

    :param client: 测试客户端。
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

    plan_id = decision_response.json()["approved_plan_id"]
    assert plan_id is not None
    return plan_id


def submit_workout(
    client: TestClient,
    user_id: str,
    plan_id: int,
    *,     #* 后面的参数必须写名字传，不能按位置传
    completed: bool = True,
    fatigue_level: int = 5,
    pain_level: int = 0,
    rpe: int = 7,
) -> None:
    response = client.post(
        f"/api/workouts/{plan_id}/sessions",
        headers={"X-User-ID": user_id},
        json={
            "completed": completed,
            "fatigue_level": fatigue_level,
            "pain_level": pain_level,
            "notes": "Weekly report seed.",
            "sets": [
                {
                    "exercise_name": "Goblet Squat",
                    "set_number": 1,
                    "weight_kg": 20,
                    "reps": 10,
                    "rpe": rpe,
                }
            ],
        },
    )
    assert response.status_code == 201


def test_weekly_report_summarizes_workouts_without_adjustment_for_safe_feedback(client: TestClient,):
    user_id = unique_user_id("weekly-safe-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)
    submit_workout(client, user_id, plan_id, completed=True, fatigue_level=5, pain_level=0, rpe=7)
    submit_workout(client, user_id, plan_id, completed=False, fatigue_level=6, pain_level=1, rpe=8)

    response = client.post(
        "/api/reports/weekly",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"] == {
        "session_count": 2,
        "completed_sessions": 1,
        "completion_rate": 0.5,
        "average_rpe": 7.5,
        "average_fatigue": 5.5,
        "max_pain": 1,
    }
    assert body["adjustment_proposal"] is None
    assert body["recommendation"] == "本周反馈整体稳定，暂时保持当前训练计划。"


def test_weekly_report_creates_lower_rpe_proposal_for_high_pain_or_fatigue(client: TestClient,):
    user_id = unique_user_id("weekly-adjust-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)
    submit_workout(client, user_id, plan_id, completed=True, fatigue_level=9, pain_level=7, rpe=9)

    response = client.post(
        "/api/reports/weekly",
        headers={"X-User-ID": user_id},
    )
    proposals_response = client.get(
        "/api/proposals",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 200
    body = response.json()
    proposal = body["adjustment_proposal"]
    assert body["metrics"]["session_count"] == 1
    assert body["metrics"]["average_fatigue"] == 9.0
    assert body["metrics"]["max_pain"] == 7
    assert body["recommendation"] == "本周疼痛或疲劳偏高，建议生成一个降低强度的训练计划草案，等待你确认。"
    assert proposal["status"] == "pending"
    assert proposal["approved_plan_id"] is None
    assert proposal["plan"]["days"][0]["exercises"][0]["target_rpe"] == 6
    assert proposals_response.status_code == 200
    assert proposals_response.json()["proposals"][0]["id"] == proposal["id"]
    assert proposal["operation"] == "replace"
    assert proposal["base_plan_id"] == plan_id
