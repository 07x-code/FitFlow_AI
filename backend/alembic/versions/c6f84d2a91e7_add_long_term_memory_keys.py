"""为长期记忆增加规范化键和 active 唯一索引。

Revision ID: c6f84d2a91e7
Revises: 874d5d9d15ba
Create Date: 2026-08-31 12:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6f84d2a91e7"
down_revision: Union[str, Sequence[str], None] = "874d5d9d15ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    增加长期记忆规范化键，并约束同一用户的 active 记忆不重复。

    :return: 无返回值。
    """
    op.add_column(
        "user_memories",
        sa.Column("memory_key", sa.String(length=160), nullable=True),
    )
    op.create_index(
        "uq_user_memories_active_key",
        "user_memories",
        ["user_id", "memory_type", "memory_key"],
        unique=True,
        postgresql_where=sa.text(
            "status = 'active' AND memory_key IS NOT NULL"
        ),
    )


def downgrade() -> None:
    """
    删除长期记忆 active 唯一索引和规范化键。

    :return: 无返回值。
    """
    op.drop_index(
        "uq_user_memories_active_key",
        table_name="user_memories",
    )
    op.drop_column("user_memories", "memory_key")
