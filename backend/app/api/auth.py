from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies import (
    get_auth_use_cases,
    get_current_user,
)
from app.application.use_cases import AuthUseCases
from app.domain.models import (
    AuthenticationResponse,
    UserAccount,
    UserLoginRequest,
    UserRegistrationRequest,
)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthenticationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserRegistrationRequest,
    response: Response,
    request: Request,
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticationResponse:
    """
    注册用户账号并写入登录 Cookie。

    :param body: 用户注册请求。
    :param response: FastAPI 响应对象。
    :param request: 当前 FastAPI 请求。
    :param use_cases: 用户认证应用用例。
    :return: 新创建的用户账号。
    """
    authenticated = await use_cases.register(body)
    _set_session_cookie(response, request, authenticated.token)
    return AuthenticationResponse(user=authenticated.user)


@router.post("/login", response_model=AuthenticationResponse)
async def login(
    body: UserLoginRequest,
    response: Response,
    request: Request,
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticationResponse:
    """
    登录用户账号并写入新的登录 Cookie。

    :param body: 用户登录请求。
    :param response: FastAPI 响应对象。
    :param request: 当前 FastAPI 请求。
    :param use_cases: 用户认证应用用例。
    :return: 已登录的用户账号。
    """
    authenticated = await use_cases.login(body)
    _set_session_cookie(response, request, authenticated.token)
    return AuthenticationResponse(user=authenticated.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> None:
    """
    删除当前登录会话和 Cookie。

    :param request: 当前 FastAPI 请求。
    :param response: FastAPI 响应对象。
    :param use_cases: 用户认证应用用例。
    :return: 无返回值。
    """
    settings = request.app.state.settings
    token = request.cookies.get(settings.session_cookie_name)
    if token is not None:
        await use_cases.logout(token)
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


@router.get("/me", response_model=UserAccount)
async def get_me(
    user: Annotated[UserAccount, Depends(get_current_user)],
) -> UserAccount:
    """
    返回当前登录用户账号。

    :param user: 当前已认证用户账号。
    :return: 当前登录用户账号。
    """
    return user


def _set_session_cookie(
    response: Response,
    request: Request,
    token: str,
) -> None:
    """
    将不透明会话令牌写入安全 Cookie。

    :param response: FastAPI 响应对象。
    :param request: 当前 FastAPI 请求。
    :param token: 新创建的登录会话令牌。
    :return: 无返回值。
    """
    settings = request.app.state.settings
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
