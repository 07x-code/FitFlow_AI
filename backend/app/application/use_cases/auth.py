from dataclasses import dataclass

from app.application.errors import ConflictError, UnauthorizedError
from app.core.passwords import hash_password, verify_password
from app.domain.models import (
    UserAccount,
    UserLoginRequest,
    UserRegistrationRequest,
    UserStatus,
)
from app.ports.repositories import DuplicateEmailError, UserRepositoryPort
from app.ports.sessions import SessionStorePort


_DUMMY_PASSWORD_HASH = hash_password("fitflow-invalid-login-password")
_INVALID_CREDENTIALS = "邮箱或密码不正确。"


@dataclass(frozen=True)
class AuthenticatedSession:
    """认证成功后创建的用户会话。"""

    user: UserAccount
    token: str


@dataclass(frozen=True)
class AuthUseCases:
    """用户注册、登录与退出应用用例。"""

    users: UserRepositoryPort
    sessions: SessionStorePort

    async def register(
        self,
        request: UserRegistrationRequest,
    ) -> AuthenticatedSession:
        """
        创建用户账号并立即建立登录会话。

        :param request: 已校验的用户注册请求。
        :return: 新用户账号和登录会话令牌。
        """
        email = str(request.email)
        if await self.users.get_by_email(email) is not None:
            raise ConflictError("该邮箱已经注册。")

        try:
            user = await self.users.create(
                email,
                hash_password(request.password),
                request.display_name,
            )
        except DuplicateEmailError as exc:
            raise ConflictError("该邮箱已经注册。") from exc

        token = await self.sessions.create(user.id)
        return AuthenticatedSession(user=user, token=token)

    async def login(
        self,
        request: UserLoginRequest,
    ) -> AuthenticatedSession:
        """
        校验账号密码并建立新的登录会话。

        :param request: 已校验的用户登录请求。
        :return: 用户账号和新登录会话令牌。
        """
        authentication = await self.users.get_authentication_by_email(
            str(request.email)
        )
        password_hash = (
            authentication[1]
            if authentication is not None
            else _DUMMY_PASSWORD_HASH
        )
        password_valid = verify_password(request.password, password_hash)

        if authentication is None or not password_valid:
            raise UnauthorizedError(_INVALID_CREDENTIALS)

        user, _ = authentication
        if user.status != UserStatus.ACTIVE:
            raise UnauthorizedError(_INVALID_CREDENTIALS)

        updated_user = await self.users.mark_login(user.id)
        if updated_user is None:
            raise UnauthorizedError(_INVALID_CREDENTIALS)

        token = await self.sessions.create(user.id)
        return AuthenticatedSession(user=updated_user, token=token)

    async def logout(self, token: str) -> None:
        """
        删除当前登录会话。

        :param token: 当前请求携带的会话令牌。
        :return: 无返回值。
        """
        await self.sessions.delete(token)
