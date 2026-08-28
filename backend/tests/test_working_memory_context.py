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

def test_coach_reuses_only_same_session_working_context(
    client: TestClient,
) -> None:
    user_id = f"working-context-user-{uuid4().hex}"
    session_id = f"working-context-session-{uuid4().hex}"
    first_message = "这一轮只讨论哑铃训练。"
    profile_response = client.post(
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
    assert profile_response.status_code == 201

    shared_headers = {
        "X-User-ID": user_id,
        "X-Session-ID": session_id,
    }
    first_response = client.post(
        "/api/coach/chat",
        headers=shared_headers,
        json={"message": first_message},
    )
    second_response = client.post(
        "/api/coach/chat",
        headers=shared_headers,
        json={"message": "我上一轮限定了什么器械？"},
    )
    isolated_response = client.post(
        "/api/coach/chat",
        headers={
            "X-User-ID": user_id,
            "X-Session-ID": f"isolated-{uuid4().hex}",
        },
        json={"message": "新会话中有什么历史？"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_message in second_response.json()["answer"]
    assert isolated_response.status_code == 200
    assert first_message not in isolated_response.json()["answer"]
