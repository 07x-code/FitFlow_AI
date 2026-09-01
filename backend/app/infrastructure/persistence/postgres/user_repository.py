from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import UserAccount, UserStatus
from app.infrastructure.persistence.postgres.models import UserRecord
from app.ports.repositories import DuplicateEmailError, UserAuthentication


class UserRepository:
    """PostgreSQL 用户账号仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        """
        创建用户账号仓储。

        :param session: 当前数据库操作使用的异步 Session。
        :return: 无返回值。
        """
        self._session = session

    async def create(
        self,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> UserAccount:
        """
        创建用户账号。

        :param email: 用户邮箱。
        :param password_hash: Argon2id 密码哈希。
        :param display_name: 用户显示名称。
        :return: 已创建的安全用户账号。
        """
        normalized_email = self._normalize_email(email)
        record = UserRecord(
            id=str(uuid4()),
            email=email.strip(),
            email_normalized=normalized_email,
            password_hash=password_hash,
            display_name=display_name.strip(),
            status=UserStatus.ACTIVE.value,
        )
        self._session.add(record)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateEmailError from exc
        await self._session.refresh(record)
        return self._to_account(record)

    async def get_by_id(self, user_id: str) -> UserAccount | None:
        """
        按用户标识查询账号。

        :param user_id: 用户标识。
        :return: 用户账号；不存在时返回 None。
        """
        record = await self._session.get(UserRecord, user_id)
        if record is None:
            return None
        return self._to_account(record)

    async def get_by_email(self, email: str) -> UserAccount | None:
        """
        按规范化邮箱查询账号。

        :param email: 用户输入的邮箱。
        :return: 用户账号；不存在时返回 None。
        """
        record = await self._get_record_by_email(email)
        if record is None:
            return None
        return self._to_account(record)

    async def get_authentication_by_email(
        self,
        email: str,
    ) -> UserAuthentication | None:
        """
        查询登录验证需要的账号和密码哈希。

        :param email: 用户输入的邮箱。
        :return: 用户账号与密码哈希；不存在时返回 None。
        """
        record = await self._get_record_by_email(email)
        if record is None:
            return None
        return self._to_account(record), record.password_hash

    async def mark_login(self, user_id: str) -> UserAccount | None:
        """
        记录用户最近登录时间。

        :param user_id: 用户标识。
        :return: 更新后的用户账号；不存在时返回 None。
        """
        record = await self._session.get(UserRecord, user_id)
        if record is None:
            return None

        record.last_login_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(record)
        return self._to_account(record)

    async def disable(self, user_id: str) -> UserAccount | None:
        """
        禁用用户账号。

        :param user_id: 用户标识。
        :return: 更新后的用户账号；不存在时返回 None。
        """
        record = await self._session.get(UserRecord, user_id)
        if record is None:
            return None

        record.status = UserStatus.DISABLED.value
        await self._session.flush()
        await self._session.refresh(record)
        return self._to_account(record)

    async def _get_record_by_email(self, email: str) -> UserRecord | None:
        """
        按规范化邮箱查询数据库记录。

        :param email: 用户输入的邮箱。
        :return: 匹配的数据库记录；不存在时返回 None。
        """
        statement = select(UserRecord).where(
            UserRecord.email_normalized == self._normalize_email(email)
        )
        return await self._session.scalar(statement)

    @staticmethod
    def _normalize_email(email: str) -> str:
        """
        生成用于唯一查询的规范化邮箱。

        :param email: 用户输入的邮箱。
        :return: 去除首尾空白并完成大小写折叠的邮箱。
        """
        return email.strip().casefold()

    @staticmethod
    def _to_account(record: UserRecord) -> UserAccount:
        """
        将数据库记录转换为不包含密码哈希的领域账号。

        :param record: PostgreSQL 用户账号记录。
        :return: 可安全提供给应用层和 API 的用户账号。
        """
        return UserAccount(
            id=record.id,
            email=record.email,
            display_name=record.display_name,
            status=UserStatus(record.status),
            email_verified_at=record.email_verified_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
            last_login_at=record.last_login_at,
        )
