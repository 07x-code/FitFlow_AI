"""为核心业务表添加常用查询索引

Revision ID: 3bf4a1b43513
Revises: 100b0b693502
Create Date: 2026-08-14 14:07:08.225168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bf4a1b43513'
down_revision: Union[str, Sequence[str], None] = '100b0b693502'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    为长期记忆、训练计划、计划提案和训练记录添加查询索引。

    :return: 无返回值。
    """
    op.create_index('ix_plan_proposals_user_parent_revision', 'training_plan_proposals', ['user_id', 'parent_proposal_id', 'revision'], unique=False)
    op.create_index('ix_plan_proposals_user_week_status', 'training_plan_proposals', ['user_id', 'target_week_start', 'status'], unique=False)
    op.create_index('ix_training_plans_user_status_week', 'training_plans', ['user_id', 'status', 'week_start'], unique=False)
    op.create_index('ix_training_plans_user_week', 'training_plans', ['user_id', 'week_start'], unique=False)
    op.create_index('ix_user_memories_user_status_id', 'user_memories', ['user_id', 'status', 'id'], unique=False)
    op.create_index('ix_workout_sessions_user_created', 'workout_sessions', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_workout_sessions_user_plan_created', 'workout_sessions', ['user_id', 'plan_id', 'created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """
    删除长期记忆、训练计划、计划提案和训练记录的查询索引。

    :return: 无返回值。
    """
    
    op.drop_index('ix_workout_sessions_user_plan_created', table_name='workout_sessions')
    op.drop_index('ix_workout_sessions_user_created', table_name='workout_sessions')
    op.drop_index('ix_user_memories_user_status_id', table_name='user_memories')
    op.drop_index('ix_training_plans_user_week', table_name='training_plans')
    op.drop_index('ix_training_plans_user_status_week', table_name='training_plans')
    op.drop_index('ix_plan_proposals_user_week_status', table_name='training_plan_proposals')
    op.drop_index('ix_plan_proposals_user_parent_revision', table_name='training_plan_proposals')
