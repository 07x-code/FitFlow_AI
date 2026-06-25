from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def unique_user_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


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


def test_coach_chat_answers_with_latest_plan_context():
    client = TestClient(app)
    user_id = unique_user_id("coach-chat-user")
    save_profile(client, user_id)
    first_plan_id = create_plan_and_get_id(client, user_id)
    latest_plan_id = create_plan_and_get_id(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers={"X-User-ID": user_id},
        json={"message": "Why is my plan 3 days per week?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_level"] == "low"
    assert body["referenced_plan_id"] == latest_plan_id
    assert body["referenced_plan_id"] != first_plan_id
    assert "Why is my plan 3 days per week?" in body["answer"]


def test_coach_chat_blocks_risky_profile_without_calling_llm():
    client = TestClient(app)
    user_id = unique_user_id("risky-coach-chat-user")
    save_profile(client, user_id, health_flags=["chest_pain"])

    response = client.post(
        "/api/coach/chat",
        headers={"X-User-ID": user_id},
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
    }


def test_coach_chat_requires_saved_profile():
    user_id = unique_user_id("missing-coach-chat-user")

    response = TestClient(app).post(
        "/api/coach/chat",
        headers={"X-User-ID": user_id},
        json={"message": "Can you explain my plan?"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found."


def test_coach_chat_returns_rpe_knowledge_source_and_uses_content_in_prompt():
    #相关问题 → 返回匹配知识
    client = TestClient(app)
    user_id = unique_user_id("coach-rag-rpe-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers={"X-User-ID": user_id},
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


def test_coach_chat_returns_no_sources_for_unrelated_question():
    #不相关问题 → 返回空知识
    client = TestClient(app)
    user_id = unique_user_id("coach-rag-unrelated-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers={"X-User-ID": user_id},
        json={"message": "Python 的装饰器是什么？"},
    )

    assert response.status_code == 200
    assert response.json()["knowledge_sources"] == []
