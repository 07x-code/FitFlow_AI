from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserStatus(StrEnum):
    """用户账号状态。"""

    ACTIVE = "active"
    DISABLED = "disabled"


class UserAccount(BaseModel):
    """可供应用层和 API 安全使用的用户账号。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=100)
    status: UserStatus
    email_verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class UserRegistrationRequest(BaseModel):
    """用户注册请求。"""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        """
        清理用户显示名称并拒绝空白内容。

        :param value: 用户提交的显示名称。
        :return: 去除首尾空白后的显示名称。
        """
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name must not be blank")
        return normalized


class UserLoginRequest(BaseModel):
    """用户登录请求。"""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthenticationResponse(BaseModel):
    """认证成功响应。"""

    model_config = ConfigDict(extra="forbid")

    user: UserAccount
