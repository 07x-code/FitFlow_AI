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
    draft_response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    assert draft_response.status_code == 201

    history_response = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": user_id},
    )
    assert history_response.status_code == 200
    return history_response.json()["plans"][0]["id"]


def test_create_training_plan_draft_returns_safe_plan_for_saved_profile():
    client = TestClient(app)
    user_id = unique_user_id("training-plan-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["plan"]["days"]) == 3
    assert body["safety_check"] == {
        "valid": True,
        "violations": [],
    }
    assert all(len(day["exercises"]) == 4 for day in body["plan"]["days"])
    assert all(
        exercise["target_rpe"] <= 8
        for day in body["plan"]["days"]
        for exercise in day["exercises"]
    )


def test_create_training_plan_draft_requires_saved_profile():
    user_id = unique_user_id("missing-training-plan-user")
    response = TestClient(app).post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found."


def test_create_training_plan_draft_blocks_risky_profile():
    client = TestClient(app)
    user_id = unique_user_id("risky-training-plan-user")
    save_profile(client, user_id, health_flags=["chest_pain"])

    response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["risk"] == {
        "level": "blocked",
        "can_auto_plan": False,
    }


def test_create_training_plan_draft_saves_each_generated_plan_to_history():
    client = TestClient(app)
    user_id = unique_user_id("history-training-plan-user")
    save_profile(client, user_id)

    first_response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    second_response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    history_response = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": user_id},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert history_response.status_code == 200
    plans = history_response.json()["plans"]
    assert len(plans) == 2
    assert plans[0]["id"] > plans[1]["id"]
    assert plans[0]["plan"]["days"][0]["name"] == "Day 1 - Full Body A"
    assert plans[0]["safety_check"] == {"valid": True, "violations": []}
    assert "created_at" in plans[0]


def test_training_plan_history_isolated_between_users():
    client = TestClient(app)
    first_user_id = unique_user_id("first-history-user")
    second_user_id = unique_user_id("second-history-user")
    save_profile(client, first_user_id)
    save_profile(client, second_user_id)

    client.post("/api/training-plans/draft", headers={"X-User-ID": first_user_id})
    client.post("/api/training-plans/draft", headers={"X-User-ID": second_user_id})
    client.post("/api/training-plans/draft", headers={"X-User-ID": second_user_id})

    first_history = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": first_user_id},
    )
    second_history = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": second_user_id},
    )

    assert first_history.status_code == 200
    assert second_history.status_code == 200
    assert len(first_history.json()["plans"]) == 1
    assert len(second_history.json()["plans"]) == 2


def test_blocked_training_plan_draft_does_not_save_history():
    client = TestClient(app)
    user_id = unique_user_id("blocked-history-user")
    save_profile(client, user_id, health_flags=["acute_injury"])

    draft_response = client.post(
        "/api/training-plans/draft",
        headers={"X-User-ID": user_id},
    )
    history_response = client.get(
        "/api/training-plans/history",
        headers={"X-User-ID": user_id},
    )

    assert draft_response.status_code == 409
    assert history_response.status_code == 200
    assert history_response.json() == {"plans": []}


def test_get_training_plan_detail_returns_owned_plan():   #自己能查看自己的训练计划
    client = TestClient(app)
    user_id = unique_user_id("detail-plan-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)

    response = client.get(
        f"/api/training-plans/{plan_id}",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == plan_id
    assert body["plan"]["days"][0]["name"] == "Day 1 - Full Body A"
    assert body["safety_check"] == {"valid": True, "violations": []}
    assert "created_at" in body


def test_get_training_plan_detail_hides_other_users_plan():   #不能查看别人的训练计划
    client = TestClient(app)
    owner_user_id = unique_user_id("detail-owner-user")
    other_user_id = unique_user_id("detail-other-user")
    save_profile(client, owner_user_id)
    save_profile(client, other_user_id)
    plan_id = create_plan_and_get_id(client, owner_user_id)

    response = client.get(
        f"/api/training-plans/{plan_id}",
        headers={"X-User-ID": other_user_id},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Training plan not found."


def test_get_training_plan_explanation_returns_rule_based_explanation():  #返回规则版训练计划解释
    client = TestClient(app)
    user_id = unique_user_id("explanation-plan-user")
    save_profile(client, user_id)
    plan_id = create_plan_and_get_id(client, user_id)

    response = client.get(
        f"/api/training-plans/{plan_id}/explanation",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan_id"] == plan_id
    assert body["summary"] == "这是一个每周 3 天的新手全身训练计划。"
    assert body["reasons"] == [
        "训练天数来自你的用户画像，每周 3 天。",
        "每天安排 4 个动作，符合新手安全范围。",
        "所有动作的目标 RPE 都不超过 8，当前计划使用 RPE 7。",
    ]
    assert body["safety_notes"] == [
        "如果出现胸痛、急性疼痛或明显不适，应停止训练并咨询专业人士。",
        "这个解释来自后端规则，后续可以交给大模型润色，但不能绕过安全规则。",
    ]


def test_get_training_plan_explanation_hides_other_users_plan():   #不能查看别人的计划解释
    client = TestClient(app)
    owner_user_id = unique_user_id("explanation-owner-user")
    other_user_id = unique_user_id("explanation-other-user")
    save_profile(client, owner_user_id)
    save_profile(client, other_user_id)
    plan_id = create_plan_and_get_id(client, owner_user_id)

    response = client.get(
        f"/api/training-plans/{plan_id}/explanation",
        headers={"X-User-ID": other_user_id},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Training plan not found."




def test_get_training_plan_detail_returns_404_for_missing_plan():   #查询不存在的训练计划返回 404
    user_id = unique_user_id("detail-missing-user")
    response = TestClient(app).get(
        "/api/training-plans/999999999",
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Training plan not found."
