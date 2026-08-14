from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Date,
    func,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.postgres.base import Base


class FitnessProfileRecord(Base):
    """用户健身画像在 PostgreSQL 中的持久化记录。"""

    __tablename__ = "fitness_profiles" #指定数据库中的真实表名为 "fitness_profiles"

    user_id: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
    )
    age: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,  #nullable=False 表示数据库不允许写入 NULL
    )
    sex: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
    height_cm: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),  #Numeric(5, 2) 表示：总共最多5位数字,小数部分最多2位
        nullable=False,
    )
    weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
    )
    goal: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    sessions_per_week: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    session_minutes: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,  #nullable=False表示数据库不允许写入 NULL
    )
    health_flags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserMemoryRecord(Base):
    """用户长期记忆在 PostgreSQL 中的持久化记录。"""

    __tablename__ = "user_memories"
    #长期记忆索引
    __table_args__ = (
        Index(
            "ix_user_memories_user_status_id",
            "user_id",
            "status",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    memory_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'active'"),
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TrainingPlanRecord(Base):
    """正式训练计划在 PostgreSQL 中的持久化记录。"""

    __tablename__ = "training_plans"

    __table_args__ = (
        Index(
            "ix_training_plans_user_week",
            "user_id",
            "week_start",
        ),
        Index(
            "ix_training_plans_user_status_week",
            "user_id",
            "status",
            "week_start",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    week_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    week_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default=text("1"),
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'scheduled'"),
    )
    source_proposal_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    plan_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    safety_check: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class TrainingPlanProposalRecord(Base):
    """大模型生成、等待用户决定的提案在 PostgreSQL 中的持久化记录。"""

    __tablename__ = "training_plan_proposals"

    __table_args__ = (
        Index(
            "ix_plan_proposals_user_week_status",
            "user_id",
            "target_week_start",
            "status",
        ),
        Index(
            "ix_plan_proposals_user_parent_revision",
            "user_id",
            "parent_proposal_id",
            "revision",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    proposal_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'training_plan'"),
    )
    operation: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
    target_week_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    base_plan_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    parent_proposal_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    revision: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default=text("1"),
    )
    status: Mapped[str] = mapped_column(    # pending/approved/rejected/superseded
        String(16),
        nullable=False,
        server_default=text("'pending'"),
    )
    plan_snapshot: Mapped[dict] = mapped_column(  #候选训练计划内容
        JSONB,
        nullable=False,
    )
    safety_check: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    generation_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    approved_plan_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    decision_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class WorkoutSessionRecord(Base):
    """训练完成记录在 PostgreSQL 中的持久化记录(训练日志)。"""

    __tablename__ = "workout_sessions"

    __table_args__ = (
        Index(
            "ix_workout_sessions_user_created",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_workout_sessions_user_plan_created",
            "user_id",
            "plan_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    plan_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    plan_day_index: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    plan_day_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    fatigue_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    pain_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sets_data: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
    )
    safety_alert: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )