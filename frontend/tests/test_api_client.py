import httpx
import pytest

from fitflow_ui.api_client import FitFlowApiClient, FitFlowApiError


def build_client(handler):
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return FitFlowApiClient(
        base_url="http://fitflow.test/",
        user_id="demo-user",
        http_client=http_client,
    )


def test_create_profile_posts_json_and_user_header():
    captured = {}

    def handler(request):
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["user_id"] = request.headers["X-User-ID"]
        captured["body"] = request.read()
        return httpx.Response(
            201,
            json={
                "profile": {"age": 22},
                "risk": {"level": "low", "can_auto_plan": True},
                "nutrition": {
                    "bmr_kcal": 1700,
                    "calorie_target_kcal": 1950,
                    "protein_target_g": 140,
                },
            },
        )

    client = build_client(handler)
    result = client.create_profile({"age": 22})

    assert captured == {
        "method": "POST",
        "path": "/api/profiles",
        "user_id": "demo-user",
        "body": b'{"age":22}',
    }
    assert result["risk"]["level"] == "low"


def test_decide_proposal_posts_expected_payload():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/api/proposals/7/decision"
        assert request.headers["X-User-ID"] == "demo-user"
        assert request.read() == (
            b'{"decision":"approve","decision_note":"Looks good."}'
        )
        return httpx.Response(
            200,
            json={
                "id": 7,
                "status": "approved",
                "approved_plan_id": 12,
            },
        )

    client = build_client(handler)
    result = client.decide_proposal(
        proposal_id=7,
        decision="approve",
        decision_note="Looks good.",
    )

    assert result["approved_plan_id"] == 12


def test_no_content_response_returns_none():
    client = build_client(lambda request: httpx.Response(204))

    assert client.request("DELETE", "/api/memories/1") is None


def test_404_becomes_readable_error():
    client = build_client(
        lambda request: httpx.Response(
            404,
            json={"detail": "Profile not found."},
        )
    )

    with pytest.raises(FitFlowApiError, match="请先完成前置步骤") as error:
        client.get_profile()

    assert error.value.status_code == 404


def test_422_lists_invalid_fields():
    client = build_client(
        lambda request: httpx.Response(
            422,
            json={
                "detail": [
                    {
                        "loc": ["body", "sessions_per_week"],
                        "msg": "Input should be less than or equal to 4",
                    }
                ]
            },
        )
    )

    with pytest.raises(FitFlowApiError, match="每周训练天数") as error:
        client.create_profile({})

    assert error.value.status_code == 422


def test_409_shows_business_error():
    client = build_client(
        lambda request: httpx.Response(
            409,
            json={"detail": "Proposal has already been decided."},
        )
    )

    with pytest.raises(FitFlowApiError, match="当前操作无法完成") as error:
        client.decide_proposal(
            proposal_id=7,
            decision="approve",
            decision_note=None,
        )

    assert error.value.status_code == 409


def test_500_mentions_dashscope_configuration():
    client = build_client(
        lambda request: httpx.Response(
            500,
            text="Internal Server Error",
        )
    )

    with pytest.raises(FitFlowApiError) as error:
        client.coach_chat("RPE 是什么？")

    assert error.value.status_code == 500
    assert "DASHSCOPE_API_KEY" in str(error.value)
    assert "FITFLOW_LLM_PROVIDER=dashscope" in str(error.value)


def test_connection_failure_becomes_readable_error():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = build_client(handler)

    with pytest.raises(FitFlowApiError, match="无法连接 FastAPI"):
        client.health()


def test_timeout_becomes_readable_error():
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    client = build_client(handler)

    with pytest.raises(FitFlowApiError, match="后端或千问响应超时"):
        client.coach_chat("RPE 是什么？")

def test_list_workout_history_filters_by_plan_id():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/api/workouts/history"
        assert request.url.params["plan_id"] == "12"
        return httpx.Response(200, json={"sessions": []})

    client = build_client(handler)

    assert client.list_workout_history(plan_id=12) == {"sessions": []}
