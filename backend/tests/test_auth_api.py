import asyncio
from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.api.dependencies import get_current_user_id
from app.core.config import AppSettings
from app.infrastructure.persistence.postgres.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgres.models import UserRecord
from app.main import app


@pytest.fixture
def auth_client() -> Iterator[TestClient]:
    """
    创建启用真实 Cookie 认证依赖的测试客户端。

    :return: FastAPI 测试客户端。
    """
    original_override = app.dependency_overrides.pop(
        get_current_user_id,
        None,
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        if original_override is not None:
            app.dependency_overrides[get_current_user_id] = original_override


def test_register_me_and_logout_use_http_only_cookie(
    auth_client: TestClient,
) -> None:
    """
    验证注册、当前用户和退出接口使用 HttpOnly Cookie 会话。

    :param auth_client: 启用真实认证依赖的测试客户端。
    :return: 无返回值。
    """
    email = f"auth-{uuid4().hex}@example.com"
    try:
        response = auth_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "FitFlow-password-2026",
                "display_name": "认证用户",
            },
        )

        assert response.status_code == 201
        assert response.json()["user"]["email"] == email
        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie
        assert "samesite=lax" in cookie
        assert "fitflow_session=" in cookie

        me_response = auth_client.get("/api/auth/me")
        assert me_response.status_code == 200
        assert me_response.json()["display_name"] == "认证用户"

        logout_response = auth_client.post("/api/auth/logout")
        assert logout_response.status_code == 204
        assert auth_client.get("/api/auth/me").status_code == 401
    finally:
        asyncio.run(_delete_user(email))


def test_login_rejects_invalid_credentials_and_duplicate_email(
    auth_client: TestClient,
) -> None:
    """
    验证登录失败响应一致且注册邮箱保持唯一。

    :param auth_client: 启用真实认证依赖的测试客户端。
    :return: 无返回值。
    """
    email = f"login-{uuid4().hex}@example.com"
    registration = {
        "email": email,
        "password": "FitFlow-password-2026",
        "display_name": "登录用户",
    }
    try:
        assert auth_client.post(
            "/api/auth/register",
            json=registration,
        ).status_code == 201
        assert auth_client.post("/api/auth/logout").status_code == 204

        duplicate = auth_client.post("/api/auth/register", json=registration)
        assert duplicate.status_code == 409

        unknown = auth_client.post(
            "/api/auth/login",
            json={"email": f"missing-{email}", "password": "wrong-password"},
        )
        wrong = auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json() == wrong.json()

        login = auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": registration["password"]},
        )
        assert login.status_code == 200
        assert login.json()["user"]["last_login_at"] is not None
    finally:
        asyncio.run(_delete_user(email))


def test_business_api_does_not_trust_user_id_header(
    auth_client: TestClient,
) -> None:
    """
    验证业务接口不会把客户端用户标识头当作登录凭据。

    :param auth_client: 启用真实认证依赖的测试客户端。
    :return: 无返回值。
    """
    response = auth_client.get(
        "/api/profiles/me",
        headers={"X-User-ID": "demo-user"},
    )

    assert response.status_code == 401


async def _delete_user(email: str) -> None:
    """
    删除认证测试创建的用户账号。

    :param email: 待删除账号的邮箱。
    :return: 无返回值。
    """
    settings = AppSettings.from_env()
    engine = create_database_engine(settings.test_database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            await session.execute(
                delete(UserRecord).where(
                    UserRecord.email_normalized == email.casefold()
                )
            )
            await session.commit()
    finally:
        await engine.dispose()
