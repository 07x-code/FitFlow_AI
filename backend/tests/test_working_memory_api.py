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

def save_profile(client: TestClient, user_id: str) -> None:
    """
    为工作记忆接口测试保存低风险用户画像。

    :param client: FastAPI 测试客户端。
    :param user_id: 用户标识。
    :return: 无返回值。
    """
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


def test_coach_records_messages_and_tool_observations_per_session(client: TestClient):
    user_id = f"working-memory-user-{uuid4().hex}"
    other_user_id = f"working-memory-other-{uuid4().hex}"
    session_id = f"session-{uuid4().hex}"
    save_profile(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers={
            "X-User-ID": user_id,
            "X-Session-ID": session_id,
        },
        json={"message": "RPE 是什么？"},
    )
    memory_response = client.get(
        f"/api/memories/working/{session_id}",
        headers={"X-User-ID": user_id},
    )
    other_user_response = client.get(
        f"/api/memories/working/{session_id}",
        headers={"X-User-ID": other_user_id},
    )

    assert response.status_code == 200
    assert memory_response.status_code == 200
    items = memory_response.json()["items"]
    assert {item["kind"] for item in items} == {
        "message",
        "tool_observation",
    }
    assert any(
        item["role"] == "user" and item["content"] == "RPE 是什么？"
        for item in items
    )
    assert any(
        item["role"] == "assistant" and item["content"] == response.json()["answer"]
        for item in items
    )
    assert {
        item["tool_name"]
        for item in items
        if item["kind"] == "tool_observation"
    } >= {
        "get_profile",
        "assess_risk",
        "retrieve_fitness_knowledge",
    }
    assert other_user_response.json() == {
        "session_id": session_id,
        "items": [],
    }


def test_end_session_immediately_clears_working_memory(client: TestClient):
    user_id = f"working-memory-clear-{uuid4().hex}"
    session_id = f"session-{uuid4().hex}"
    save_profile(client, user_id)
    headers = {
        "X-User-ID": user_id,
        "X-Session-ID": session_id,
    }
    chat_response = client.post(
        "/api/coach/chat",
        headers=headers,
        json={"message": "解释一下我的训练安排"},
    )
    assert chat_response.status_code == 200

    end_response = client.delete(
        f"/api/memories/working/{session_id}",
        headers={"X-User-ID": user_id},
    )
    list_response = client.get(
        f"/api/memories/working/{session_id}",
        headers={"X-User-ID": user_id},
    )

    assert end_response.status_code == 204
    assert list_response.json()["items"] == []


def test_coach_requires_session_id_header(client: TestClient):
    response = client.post(
        "/api/coach/chat",
        headers={"X-User-ID": "missing-session-user"},
        json={"message": "hello"},
    )

    assert response.status_code == 422
