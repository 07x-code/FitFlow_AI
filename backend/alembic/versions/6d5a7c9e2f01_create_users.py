"""创建用户账号表并保留现有业务数据归属。

Revision ID: 6d5a7c9e2f01
Revises: c6f84d2a91e7
Create Date: 2026-09-01 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6d5a7c9e2f01"
down_revision: Union[str, Sequence[str], None] = "c6f84d2a91e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    创建用户账号表，并为现有业务用户建立禁用的历史账号。

    :return: 无返回值。
    """
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "email_normalized",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "email_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'disabled')",
            name="ck_users_status_allowed",
        ),
        sa.CheckConstraint(
            "char_length(trim(email)) BETWEEN 3 AND 320",
            name="ck_users_email_length",
        ),
        sa.CheckConstraint(
            "char_length(trim(email_normalized)) BETWEEN 3 AND 320",
            name="ck_users_normalized_email_length",
        ),
        sa.CheckConstraint(
            "char_length(trim(display_name)) BETWEEN 1 AND 100",
            name="ck_users_display_name_length",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "email_normalized",
            name="uq_users_email_normalized",
        ),
    )

    op.execute(
        """
        INSERT INTO users (
            id,
            email,
            email_normalized,
            password_hash,
            display_name,
            status
        )
        SELECT
            legacy.user_id,
            'legacy+' || md5(legacy.user_id) || '@invalid.fitflow.local',
            'legacy+' || md5(legacy.user_id) || '@invalid.fitflow.local',
            '!',
            '历史用户',
            'disabled'
        FROM (
            SELECT user_id FROM fitness_profiles
            UNION
            SELECT user_id FROM user_memories
            UNION
            SELECT user_id FROM training_plans
            UNION
            SELECT user_id FROM training_plan_proposals
            UNION
            SELECT user_id FROM workout_sessions
        ) AS legacy
        WHERE legacy.user_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    """
    删除用户账号表。

    :return: 无返回值。
    """
    op.drop_table("users")
