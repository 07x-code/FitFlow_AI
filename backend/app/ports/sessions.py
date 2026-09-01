from typing import Protocol


class SessionStorePort(Protocol):
    """登录会话存储端口。"""

    async def create(self, user_id: str) -> str:
        """
        为用户创建新的不透明会话令牌。

        :param user_id: 用户标识。
        :return: 仅交付给客户端 Cookie 的会话令牌。
        """
        ...

    async def get_user_id(self, token: str) -> str | None:
        """
        解析有效会话并刷新空闲过期时间。

        :param token: 客户端提交的会话令牌。
        :return: 会话所属用户标识；会话无效时返回 None。
        """
        ...

    async def delete(self, token: str) -> None:
        """
        删除指定登录会话。

        :param token: 客户端提交的会话令牌。
        :return: 无返回值。
        """
        ...

    async def ping(self) -> None:
        """
        检查会话存储是否可用。

        :return: 无返回值。
        """
        ...

    async def close(self) -> None:
        """
        释放会话存储使用的资源。

        :return: 无返回值。
        """
        ...
