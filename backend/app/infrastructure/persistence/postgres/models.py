from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Date,
    func,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.postgres.base import Base


class UserRecord(Base):
    """用户账号在 PostgreSQL 中的持久化记录。"""

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'disabled')",
            name="ck_users_status_allowed",
        ),
        CheckConstraint(
            "char_length(trim(email)) BETWEEN 3 AND 320",
            name="ck_users_email_length",
        ),
        CheckConstraint(
            "char_length(trim(email_normalized)) BETWEEN 3 AND 320",
            name="ck_users_normalized_email_length",
        ),
        CheckConstraint(
            "char_length(trim(display_name)) BETWEEN 1 AND 100",
            name="ck_users_display_name_length",
        ),
        UniqueConstraint(
            "email_normalized",
            name="uq_users_email_normalized",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )
    email_normalized: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
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
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class FitnessProfileRecord(Base):
    """用户健身画像在 PostgreSQL 中的持久化记录。"""

    __tablename__ = "fitness_profiles" #指定数据库中的真实表名为 "fitness_profiles"

    __table_args__ = (
        CheckConstraint(
            "age BETWEEN 16 AND 80",
            name="ck_fitness_profiles_age_range",
        ),
        CheckConstraint(
            "sex IN ('male', 'female')",
            name="ck_fitness_profiles_sex_allowed",
        ),
        CheckConstraint(
            "height_cm BETWEEN 120 AND 230",
            name="ck_fitness_profiles_height_range",
        ),
        CheckConstraint(
            "weight_kg BETWEEN 35 AND 250",
            name="ck_fitness_profiles_weight_range",
        ),
        CheckConstraint(
            "goal IN ('fat_loss', 'muscle_gain', 'general_fitness')",
            name="ck_fitness_profiles_goal_allowed",
        ),
        CheckConstraint(
            "sessions_per_week BETWEEN 2 AND 4",
            name="ck_fitness_profiles_sessions_range",
        ),
        CheckConstraint(
            "session_minutes BETWEEN 30 AND 120",
            name="ck_fitness_profiles_session_minutes_range",
        ),
    )

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

    
    
    __table_args__ = (
        CheckConstraint(
            """
            memory_type IN (
                'preferred_equipment',
                'disliked_exercise',
                'training_time',
                'physical_limitation',
                'general_note'
            )
            """,
            name="ck_user_memories_type_allowed",
        ),
        CheckConstraint(
            "source IN ('user', 'profile', 'approved_proposal')",
            name="ck_user_memories_source_allowed",
        ),
        CheckConstraint(
            "status IN ('active', 'deleted')",
            name="ck_user_memories_status_allowed",
        ),
        CheckConstraint(
            "char_length(content) BETWEEN 1 AND 500",
            name="ck_user_memories_content_length",
        ),
        #长期记忆索引
        Index(
            "ix_user_memories_user_status_id",
            "user_id",
            "status",
            "id",
        ),
        Index(
            "uq_user_memories_active_key",
            "user_id",
            "memory_type",
            "memory_key",
            unique=True,
            postgresql_where=text(
                "status = 'active' AND memory_key IS NOT NULL"
            ),
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
    memory_key: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
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

        CheckConstraint(
            "week_end = week_start + 6",
            name="ck_training_plans_week_range",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_training_plans_version_positive",
        ),
        CheckConstraint(
            """
            status IN (
                'scheduled',
                'active',
                'superseded',
                'completed'
            )
            """,
            name="ck_training_plans_status_allowed",
        ),
        UniqueConstraint(
            "user_id",
            "week_start",
            "version",
            name="uq_training_plans_user_week_version",
        ),
        UniqueConstraint(
            "source_proposal_id",
            name="uq_training_plans_source_proposal",
        ),


        Index(
            "uq_training_plans_user_week_current",
            "user_id",
            "week_start",
            unique=True,
            postgresql_where=text(
                "status IN ('scheduled', 'active')"
            ),    #postgresql_where=只有满足这个条件的数据行，才放进该索引。
        ),


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
        ForeignKey(
            "training_plan_proposals.id", #保证正式计划可以追溯到用户批准的 Proposal
            name="fk_training_plans_source_proposal",
            use_alter=True,  #先建表，再补其中一条外键
            ondelete="RESTRICT",
        ),
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
        CheckConstraint(
            "proposal_type = 'training_plan'",
            name="ck_plan_proposals_type_allowed",
        ),
        CheckConstraint(
            "operation IN ('create', 'replace', 'adjust')",
            name="ck_plan_proposals_operation_allowed",
        ),
        CheckConstraint(
            """
            status IN (
                'pending',
                'approving',
                'approved',
                'rejected',
                'superseded'
            )
            """,
            name="ck_plan_proposals_status_allowed",
        ),
        CheckConstraint(
            "revision >= 1",
            name="ck_plan_proposals_revision_positive",
        ),
        UniqueConstraint(
            "user_id",
            "parent_proposal_id",
            "revision",
            name="uq_plan_proposals_user_parent_revision",
        ),
        UniqueConstraint(
            "approved_plan_id",
            name="uq_plan_proposals_approved_plan",
        ),

        Index(
            "uq_plan_proposals_user_week_pending",
            "user_id",
            "target_week_start",
            unique=True,
            postgresql_where=text(
                "status IN ('pending', 'approving')"
            ),
        ),



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
        ForeignKey(
            "training_plans.id",
            name="fk_plan_proposals_base_plan",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    parent_proposal_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "training_plan_proposals.id",
            name="fk_plan_proposals_parent",
            ondelete="RESTRICT",
        ),
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
        ForeignKey(
            "training_plans.id",
            name="fk_plan_proposals_approved_plan",
            ondelete="RESTRICT",
        ),
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

        CheckConstraint(
            "plan_day_index BETWEEN 1 AND 7",
            name="ck_workout_sessions_plan_day_range",
        ),
        CheckConstraint(
            "fatigue_level BETWEEN 1 AND 10",
            name="ck_workout_sessions_fatigue_range",
        ),
        CheckConstraint(
            "pain_level BETWEEN 0 AND 10",
            name="ck_workout_sessions_pain_range",
        ),
        CheckConstraint(
            "notes IS NULL OR char_length(notes) <= 1000",
            name="ck_workout_sessions_notes_length",
        ),
        CheckConstraint(
            """
            jsonb_typeof(sets_data) = 'array'
            AND jsonb_array_length(sets_data) >= 1
            """,
            name="ck_workout_sessions_sets_nonempty_array",
        ),

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
        ForeignKey(
            "training_plans.id",
            name="fk_workout_sessions_plan",
            ondelete="RESTRICT",
        ),
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
