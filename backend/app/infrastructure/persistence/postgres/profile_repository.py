from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.profile import FitnessGoal, FitnessProfileCreate, Sex
from app.infrastructure.persistence.postgres.models import FitnessProfileRecord


class ProfileRepository:
    """PostgreSQL 用户健身画像仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        """
        创建用户健身画像仓储。

        :param session: 当前数据库操作使用的异步 Session。
        :return: 无返回值。
        """
        self._session = session

    async def save(
        self,
        user_id: str,
        profile: FitnessProfileCreate,
    ) -> None:
        """
        新增或更新用户健身画像。

        :param user_id: 用户标识。
        :param profile: 已校验的健身画像。
        :return: 无返回值。
        """
        record = await self._session.get(FitnessProfileRecord, user_id)

        if record is None:
            record = FitnessProfileRecord(user_id=user_id)
            self._session.add(record)

        record.age = profile.age
        record.sex = profile.sex.value
        record.height_cm = profile.height_cm
        record.weight_kg = profile.weight_kg
        record.goal = profile.goal.value
        record.sessions_per_week = profile.sessions_per_week
        record.session_minutes = profile.session_minutes
        record.health_flags = list(profile.health_flags)

        await self._session.flush()

    async def get(self, user_id: str) -> FitnessProfileCreate | None:
        """
        查询指定用户的健身画像。

        :param user_id: 用户标识。
        :return: 用户健身画像；不存在时返回 None。
        """
        record = await self._session.get(FitnessProfileRecord, user_id)
        if record is None:
            return None

        return FitnessProfileCreate(
            age=record.age,
            sex=Sex(record.sex),
            height_cm=float(record.height_cm),
            weight_kg=float(record.weight_kg),
            goal=FitnessGoal(record.goal),
            sessions_per_week=record.sessions_per_week,
            session_minutes=record.session_minutes,
            health_flags=list(record.health_flags),
        )