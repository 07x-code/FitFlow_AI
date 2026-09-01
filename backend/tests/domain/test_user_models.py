from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.models import (
    UserAccount,
    UserLoginRequest,
    UserRegistrationRequest,
    UserStatus,
)


def test_user_account_exposes_only_safe_account_fields() -> None:
    """
    验证用户账号模型包含公开字段且不接受密码哈希。

    :return: 无返回值。
    """
    now = datetime.now(timezone.utc)
    account = UserAccount(
        id="4e508068-79dd-4782-ae5a-7b77c84146fc",
        email="user@example.com",
        display_name="训练用户",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )

    assert account.status == UserStatus.ACTIVE
    assert "password_hash" not in account.model_dump()

    with pytest.raises(ValidationError):
        UserAccount(
            id=account.id,
            email=account.email,
            display_name=account.display_name,
            status=account.status,
            created_at=now,
            updated_at=now,
            password_hash="must-not-be-exposed",
        )


def test_registration_request_validates_identity_fields() -> None:
    """
    验证注册请求会校验邮箱、密码长度和显示名称。

    :return: 无返回值。
    """
    request = UserRegistrationRequest(
        email="Athlete@Example.com",
        password="fitflow-password",
        display_name="  小林  ",
    )

    assert str(request.email) == "Athlete@example.com"
    assert request.display_name == "小林"

    with pytest.raises(ValidationError):
        UserRegistrationRequest(
            email="invalid-email",
            password="short",
            display_name=" ",
        )


def test_login_request_accepts_existing_account_credentials() -> None:
    """
    验证登录请求只要求有效邮箱和非空密码。

    :return: 无返回值。
    """
    request = UserLoginRequest(
        email="athlete@example.com",
        password="x",
    )

    assert str(request.email) == "athlete@example.com"
    assert request.password == "x"
