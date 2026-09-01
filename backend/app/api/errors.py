from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.errors import (
    ApplicationError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    UnauthorizedError,
    UnprocessableError,
)


ERROR_STATUS_CODES: dict[type[ApplicationError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidRequestError: status.HTTP_400_BAD_REQUEST,
    UnprocessableError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
}


def register_application_error_handlers(app: FastAPI) -> None:
    """
    将应用层异常统一转换为 HTTP 错误响应。

    :param app: FastAPI 应用实例。
    :return: 无返回值。
    """

    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        _request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        status_code = ERROR_STATUS_CODES.get(
            type(exc),
            status.HTTP_400_BAD_REQUEST,
        )
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.detail},
        )
