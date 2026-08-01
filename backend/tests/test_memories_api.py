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


def test_create_and_list_user_memories():
    client = TestClient(app)
    user_id = unique_user_id("memory-user")

    response = client.post(
        "/api/memories",
        headers={"X-User-ID": user_id},
        json={
            "type": "preferred_equipment",
            "content": "I prefer dumbbells for upper body workouts.",
        },
    )
    list_response = client.get(
        "/api/memories",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "preferred_equipment"
    assert body["content"] == "I prefer dumbbells for upper body workouts."
    assert body["source"] == "user"
    assert "created_at" in body
    assert list_response.status_code == 200
    assert list_response.json()["memories"][0]["id"] == body["id"]


def test_delete_memory_removes_only_owned_memory():
    client = TestClient(app)
    owner_user_id = unique_user_id("memory-owner")
    other_user_id = unique_user_id("memory-other")
    create_response = client.post(
        "/api/memories",
        headers={"X-User-ID": owner_user_id},
        json={"type": "disliked_exercise", "content": "I dislike burpees."},
    )
    memory_id = create_response.json()["id"]

    other_delete_response = client.delete(
        f"/api/memories/{memory_id}",
        headers={"X-User-ID": other_user_id},
    )
    owner_delete_response = client.delete(
        f"/api/memories/{memory_id}",
        headers={"X-User-ID": owner_user_id},
    )
    list_response = client.get(
        "/api/memories",
        headers={"X-User-ID": owner_user_id},
    )

    assert other_delete_response.status_code == 404
    assert other_delete_response.json()["detail"] == "Memory not found."
    assert owner_delete_response.status_code == 204
    assert list_response.json() == {"memories": []}


def test_coach_chat_includes_user_memories_in_prompt():
    client = TestClient(app)
    user_id = unique_user_id("memory-chat-user")
    save_profile(client, user_id)
    memory_content = "I prefer dumbbells for upper body workouts."
    memory_response = client.post(
        "/api/memories",
        headers={"X-User-ID": user_id},
        json={"type": "preferred_equipment", "content": memory_content},
    )
    assert memory_response.status_code == 201

    chat_response = client.post(
        "/api/coach/chat",
        headers={
            "X-User-ID": user_id,
            "X-Session-ID": f"session-{uuid4().hex}",
        },
        json={"message": "Can you adapt my next workout?"},
    )

    assert chat_response.status_code == 200
    assert memory_content in chat_response.json()["answer"]
