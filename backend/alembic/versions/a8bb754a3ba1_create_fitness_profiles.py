"""创建用户健身画像表。

Revision ID: a8bb754a3ba1
Revises:
Create Date: 2026-08-10 18:35:55.613691
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a8bb754a3ba1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    创建用户健身画像表。

    :return: 无返回值。
    """
    op.create_table('fitness_profiles',
    sa.Column('user_id', sa.String(length=128), nullable=False),
    sa.Column('age', sa.SmallInteger(), nullable=False),
    sa.Column('sex', sa.String(length=16), nullable=False),
    sa.Column('height_cm', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('weight_kg', sa.Numeric(precision=6, scale=2), nullable=False),
    sa.Column('goal', sa.String(length=32), nullable=False),
    sa.Column('sessions_per_week', sa.SmallInteger(), nullable=False),
    sa.Column('session_minutes', sa.SmallInteger(), nullable=False),
    sa.Column('health_flags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('user_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """
    删除用户健身画像表。

    :return: 无返回值。
    """
    op.drop_table('fitness_profiles')
    # ### end Alembic commands ###
