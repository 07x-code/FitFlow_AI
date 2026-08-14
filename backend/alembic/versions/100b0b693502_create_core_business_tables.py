"""创建训练计划相关的核心业务表。

Revision ID: 100b0b693502
Revises: a8bb754a3ba1
Create Date: 2026-08-13 13:21:34.710875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '100b0b693502'
down_revision: Union[str, Sequence[str], None] = 'a8bb754a3ba1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    创建长期记忆、训练计划、计划提案和训练记录表。

    :return: 无返回值。
    """
    op.create_table('training_plan_proposals',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=128), nullable=False),
    sa.Column('proposal_type', sa.String(length=32), server_default=sa.text("'training_plan'"), nullable=False),
    sa.Column('operation', sa.String(length=16), nullable=False),
    sa.Column('target_week_start', sa.Date(), nullable=False),
    sa.Column('base_plan_id', sa.BigInteger(), nullable=True),
    sa.Column('parent_proposal_id', sa.BigInteger(), nullable=True),
    sa.Column('revision', sa.SmallInteger(), server_default=sa.text('1'), nullable=False),
    sa.Column('status', sa.String(length=16), server_default=sa.text("'pending'"), nullable=False),
    sa.Column('plan_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('safety_check', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('generation_summary', sa.Text(), nullable=False),
    sa.Column('approved_plan_id', sa.BigInteger(), nullable=True),
    sa.Column('decision_note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('training_plans',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=128), nullable=False),
    sa.Column('week_start', sa.Date(), nullable=False),
    sa.Column('week_end', sa.Date(), nullable=False),
    sa.Column('timezone', sa.String(length=64), nullable=False),
    sa.Column('version', sa.SmallInteger(), server_default=sa.text('1'), nullable=False),
    sa.Column('status', sa.String(length=16), server_default=sa.text("'scheduled'"), nullable=False),
    sa.Column('source_proposal_id', sa.BigInteger(), nullable=False),
    sa.Column('plan_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('safety_check', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_memories',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=128), nullable=False),
    sa.Column('memory_type', sa.String(length=32), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('source', sa.String(length=32), nullable=False),
    sa.Column('status', sa.String(length=16), server_default=sa.text("'active'"), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('workout_sessions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=128), nullable=False),
    sa.Column('plan_id', sa.BigInteger(), nullable=False),
    sa.Column('plan_day_index', sa.SmallInteger(), nullable=False),
    sa.Column('plan_day_name', sa.String(length=128), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.Column('fatigue_level', sa.SmallInteger(), nullable=False),
    sa.Column('pain_level', sa.SmallInteger(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('sets_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('safety_alert', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )



def downgrade() -> None:
    """
    删除长期记忆、训练计划、计划提案和训练记录表。

    :return: 无返回值。
    """

    op.drop_table('workout_sessions')
    op.drop_table('user_memories')
    op.drop_table('training_plans')
    op.drop_table('training_plan_proposals')
