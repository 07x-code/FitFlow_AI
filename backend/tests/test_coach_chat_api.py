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


def coach_headers(user_id: str) -> dict[str, str]:
    return {
        "X-User-ID": user_id,
        "X-Session-ID": f"session-{uuid4().hex}",
    }


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


def test_coach_chat_answers_with_latest_plan_context(client: TestClient):
    user_id = unique_user_id("coach-chat-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers=coach_headers(user_id),
        json={"message": "Why is my plan 3 days per week?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_level"] == "low"
    assert body["referenced_plan_id"] == plan_id
    assert "Why is my plan 3 days per week?" in body["answer"]


def test_coach_chat_blocks_risky_profile_without_calling_llm(client: TestClient):
    user_id = unique_user_id("risky-coach-chat-user")
    save_profile(client, user_id, health_flags=["chest_pain"])

    response = client.post(
        "/api/coach/chat",
        headers=coach_headers(user_id),
        json={"message": "Can I train chest today?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "answer": (
            "你的健康风险等级为 blocked，系统不会提供自动训练建议。"
            "如果出现胸痛、急性损伤或明显不适，请停止训练并咨询专业人士。"
        ),
        "safety_level": "blocked",
        "referenced_plan_id": None,
        "knowledge_sources": [],
        "memory_events": [],
    }


def test_coach_chat_requires_saved_profile(client: TestClient):
    user_id = unique_user_id("missing-coach-chat-user")

    response = client.post(
        "/api/coach/chat",
        headers=coach_headers(user_id),
        json={"message": "Can you explain my plan?"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found."


def test_coach_chat_returns_rpe_knowledge_source_and_uses_content_in_prompt(client: TestClient):
    user_id = unique_user_id("coach-rag-rpe-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers=coach_headers(user_id),
        json={"message": "RPE 是什么？"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["knowledge_sources"] == [
        {
            "title": "RPE 基础说明",
            "category": "训练强度",
            "summary": "使用 RPE 衡量训练强度，初学者通常无需频繁练到力竭。",
        }
    ]
    assert "RPE 7 表示大约还能完成 3 次重复" in body["answer"]


def test_coach_chat_returns_no_sources_for_unrelated_question(client: TestClient):
    user_id = unique_user_id("coach-rag-unrelated-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers=coach_headers(user_id),
        json={"message": "Python 的装饰器是什么？"},
    )

    assert response.status_code == 200
    assert response.json()["knowledge_sources"] == []


def test_coach_chat_saves_and_deduplicates_explicit_long_term_memory(
    client: TestClient,
) -> None:
    """
    验证 Coach 自动保存明确偏好，并避免生成重复 active 记忆。

    :param client: 已连接测试数据库的客户端。
    :return: 无返回值。
    """
    user_id = unique_user_id("coach-memory-user")
    save_profile(client, user_id)
    headers = coach_headers(user_id)

    first = client.post(
        "/api/coach/chat",
        headers=headers,
        json={"message": "我不喜欢飞鸟，以后别安排。"},
    )
    second = client.post(
        "/api/coach/chat",
        headers=headers,
        json={"message": "我不喜欢飞鸟。"},
    )
    memories = client.get(
        "/api/memories",
        headers={"X-User-ID": user_id},
    )

    assert first.status_code == 200
    assert first.json()["memory_events"] == [
        {
            "action": "remembered",
            "memory_id": first.json()["memory_events"][0]["memory_id"],
            "type": "disliked_exercise",
            "content": "以后不安排飞鸟。",
        }
    ]
    assert second.status_code == 200
    assert second.json()["memory_events"] == []
    assert memories.status_code == 200
    assert [item["content"] for item in memories.json()["memories"]] == [
        "以后不安排飞鸟。"
    ]


def test_coach_chat_forgets_explicit_long_term_memory(
    client: TestClient,
) -> None:
    """
    验证用户改变动作偏好后停用对应长期记忆。

    :param client: 已连接测试数据库的客户端。
    :return: 无返回值。
    """
    user_id = unique_user_id("coach-forget-memory-user")
    save_profile(client, user_id)
    headers = coach_headers(user_id)
    client.post(
        "/api/coach/chat",
        headers=headers,
        json={"message": "我不喜欢飞鸟。"},
    )

    response = client.post(
        "/api/coach/chat",
        headers=headers,
        json={"message": "我现在喜欢飞鸟了。"},
    )
    memories = client.get(
        "/api/memories",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 200
    assert response.json()["memory_events"][0]["action"] == "forgotten"
    assert response.json()["memory_events"][0]["content"] == "已不再排除飞鸟。"
    assert memories.json() == {"memories": []}
