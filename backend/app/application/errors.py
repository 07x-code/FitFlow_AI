from typing import Any


class ApplicationError(Exception):
    """应用用例执行失败。"""

    def __init__(self, detail: Any) -> None:
        self.detail = detail
        super().__init__(str(detail))


class NotFoundError(ApplicationError):
    """应用资源不存在或不属于当前用户。"""


class ConflictError(ApplicationError):
    """当前资源状态与操作发生冲突。"""


class InvalidRequestError(ApplicationError):
    """请求违反应用规则。"""


class UnprocessableError(ApplicationError):
    """请求格式正确，但生成结果未通过业务校验。"""


class UnauthorizedError(ApplicationError):
    """当前请求未通过身份认证。"""
