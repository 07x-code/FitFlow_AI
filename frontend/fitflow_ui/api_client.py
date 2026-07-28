from typing import Any

import httpx


FIELD_LABELS = {
    "age": "年龄",
    "sex": "性别",
    "height_cm": "身高",
    "weight_kg": "体重",
    "goal": "健身目标",
    "sessions_per_week": "每周训练天数",
    "session_minutes": "单次训练时长",
    "health_flags": "健康风险标记",
    "fatigue_level": "疲劳程度",
    "pain_level": "疼痛程度",
    "sets": "动作组记录",
}


class FitFlowApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


class FitFlowApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        user_id: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self._client = http_client or httpx.Client(
            timeout=httpx.Timeout(
                connect=2.0,
                read=40.0,
                write=10.0,
                pool=5.0,
            )
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = self._client.request(
                method,
                f"{self.base_url}{path}",
                headers={"X-User-ID": self.user_id},
                json=json,
            )
        except httpx.ConnectError as exc:
            raise FitFlowApiError(
                "无法连接 FastAPI，请先运行：uvicorn app.main:app --reload"
            ) from exc
        except httpx.TimeoutException as exc:
            raise FitFlowApiError(
                "后端或千问响应超时，请稍后重试并检查模型配置。"
            ) from exc
        except httpx.HTTPError as exc:
            raise FitFlowApiError(f"HTTP 请求失败：{exc}") from exc

        if response.status_code == 204:
            return None
        if response.is_error:
            raise _build_api_error(response)

        try:
            return response.json()
        except ValueError as exc:
            raise FitFlowApiError(
                "后端返回了无法解析的响应。",
                status_code=response.status_code,
            ) from exc

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/health")

    def create_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/api/profiles", json=payload)

    def get_profile(self) -> dict[str, Any]:
        return self.request("GET", "/api/profiles/me")

    def create_training_plan_proposal(self) -> dict[str, Any]:
        return self.request("POST", "/api/proposals/training-plan")

    def list_proposals(self) -> dict[str, Any]:
        return self.request("GET", "/api/proposals")

    def decide_proposal(
        self,
        *,
        proposal_id: int,
        decision: str,
        decision_note: str | None,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/proposals/{proposal_id}/decision",
            json={
                "decision": decision,
                "decision_note": decision_note or None,
            },
        )

    def list_training_plans(self) -> dict[str, Any]:
        return self.request("GET", "/api/training-plans/history")

    def create_workout_session(
        self,
        *,
        plan_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            f"/api/workouts/{plan_id}/sessions",
            json=payload,
        )

    def list_workout_history(
        self,
        *,
        plan_id: int | None = None,
    ) -> dict[str, Any]:
        path = "/api/workouts/history"
        if plan_id is not None:
            path += f"?plan_id={plan_id}"
        return self.request("GET", path)

    def create_weekly_report(self) -> dict[str, Any]:
        return self.request("POST", "/api/reports/weekly")

    def coach_chat(self, message: str) -> dict[str, Any]:
        return self.request(
            "POST",
            "/api/coach/chat",
            json={"message": message},
        )


def _build_api_error(response: httpx.Response) -> FitFlowApiError:
    try:
        body = response.json()
    except ValueError:
        body = {}

    detail = body.get("detail") if isinstance(body, dict) else None
    if response.status_code == 404:
        message = (
            "请先完成前置步骤，或确认当前用户拥有这条数据。"
            f" 后端信息：{_detail_text(detail)}"
        )
    elif response.status_code == 422:
        message = _format_validation_error(detail)
    elif response.status_code in {400, 409}:
        message = f"当前操作无法完成：{_detail_text(detail)}"
    elif response.status_code >= 500:
        message = (
            "后端服务异常。如果正在使用千问，请检查 "
            "DASHSCOPE_API_KEY 和 FITFLOW_LLM_PROVIDER=dashscope。"
        )
    else:
        message = (
            f"请求失败（HTTP {response.status_code}）：{_detail_text(detail)}"
        )

    return FitFlowApiError(message, status_code=response.status_code)


def _format_validation_error(detail: Any) -> str:
    if not isinstance(detail, list):
        return f"输入数据校验失败：{_detail_text(detail)}"

    messages = []
    for error in detail:
        if not isinstance(error, dict):
            messages.append(_detail_text(error))
            continue

        location = error.get("loc", [])
        field = str(location[-1]) if location else "unknown"
        label = FIELD_LABELS.get(field, field)
        messages.append(f"{label}：{error.get('msg', '输入不合法')}")

    return "输入数据校验失败：" + "；".join(messages)


def _detail_text(detail: Any) -> str:
    if isinstance(detail, dict):
        return str(detail.get("message", detail))
    return str(detail or "未知错误")
