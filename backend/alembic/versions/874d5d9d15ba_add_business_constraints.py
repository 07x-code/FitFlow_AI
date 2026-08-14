"""为核心业务表添加业务约束。

Revision ID: 874d5d9d15ba
Revises: 3bf4a1b43513
Create Date: 2026-08-14 21:02:55.861669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '874d5d9d15ba'
down_revision: Union[str, Sequence[str], None] = '3bf4a1b43513'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    添加核心业务表的检查约束、唯一约束、部分唯一索引和外键。

    :return: 无返回值。
    """
    op.create_check_constraint('ck_fitness_profiles_age_range', 'fitness_profiles', 'age BETWEEN 16 AND 80')
    op.create_check_constraint('ck_fitness_profiles_goal_allowed', 'fitness_profiles', "goal IN ('fat_loss', 'muscle_gain', 'general_fitness')")
    op.create_check_constraint('ck_fitness_profiles_height_range', 'fitness_profiles', 'height_cm BETWEEN 120 AND 230')
    op.create_check_constraint('ck_fitness_profiles_session_minutes_range', 'fitness_profiles', 'session_minutes BETWEEN 30 AND 120')
    op.create_check_constraint('ck_fitness_profiles_sessions_range', 'fitness_profiles', 'sessions_per_week BETWEEN 2 AND 4')
    op.create_check_constraint('ck_fitness_profiles_sex_allowed', 'fitness_profiles', "sex IN ('male', 'female')")
    op.create_check_constraint('ck_fitness_profiles_weight_range', 'fitness_profiles', 'weight_kg BETWEEN 35 AND 250')
    op.create_unique_constraint('uq_plan_proposals_approved_plan', 'training_plan_proposals', ['approved_plan_id'])
    op.create_unique_constraint('uq_plan_proposals_user_parent_revision', 'training_plan_proposals', ['user_id', 'parent_proposal_id', 'revision'])
    op.create_index('uq_plan_proposals_user_week_pending', 'training_plan_proposals', ['user_id', 'target_week_start'], unique=True, postgresql_where=sa.text("status IN ('pending', 'approving')"))
    op.create_foreign_key('fk_plan_proposals_base_plan', 'training_plan_proposals', 'training_plans', ['base_plan_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('fk_plan_proposals_parent', 'training_plan_proposals', 'training_plan_proposals', ['parent_proposal_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('fk_plan_proposals_approved_plan', 'training_plan_proposals', 'training_plans', ['approved_plan_id'], ['id'], ondelete='RESTRICT')
    op.create_check_constraint('ck_plan_proposals_operation_allowed', 'training_plan_proposals', "operation IN ('create', 'replace', 'adjust')")
    op.create_check_constraint('ck_plan_proposals_revision_positive', 'training_plan_proposals', 'revision >= 1')
    op.create_check_constraint('ck_plan_proposals_status_allowed', 'training_plan_proposals', "\n            status IN (\n                'pending',\n                'approving',\n                'approved',\n                'rejected',\n                'superseded'\n            )\n            ")
    op.create_check_constraint('ck_plan_proposals_type_allowed', 'training_plan_proposals', "proposal_type = 'training_plan'")
    op.create_unique_constraint('uq_training_plans_source_proposal', 'training_plans', ['source_proposal_id'])
    op.create_index('uq_training_plans_user_week_current', 'training_plans', ['user_id', 'week_start'], unique=True, postgresql_where=sa.text("status IN ('scheduled', 'active')"))
    op.create_unique_constraint('uq_training_plans_user_week_version', 'training_plans', ['user_id', 'week_start', 'version'])
    op.create_foreign_key('fk_training_plans_source_proposal', 'training_plans', 'training_plan_proposals', ['source_proposal_id'], ['id'], ondelete='RESTRICT', use_alter=True)
    op.create_check_constraint('ck_training_plans_status_allowed', 'training_plans', "\n            status IN (\n                'scheduled',\n                'active',\n                'superseded',\n                'completed'\n            )\n            ")
    op.create_check_constraint('ck_training_plans_version_positive', 'training_plans', 'version >= 1')
    op.create_check_constraint('ck_training_plans_week_range', 'training_plans', 'week_end = week_start + 6')
    op.create_check_constraint('ck_user_memories_content_length', 'user_memories', 'char_length(content) BETWEEN 1 AND 500')
    op.create_check_constraint('ck_user_memories_source_allowed', 'user_memories', "source IN ('user', 'profile', 'approved_proposal')")
    op.create_check_constraint('ck_user_memories_status_allowed', 'user_memories', "status IN ('active', 'deleted')")
    op.create_check_constraint('ck_user_memories_type_allowed', 'user_memories', "\n            memory_type IN (\n                'preferred_equipment',\n                'disliked_exercise',\n                'training_time',\n                'physical_limitation',\n                'general_note'\n            )\n            ")
    op.create_foreign_key('fk_workout_sessions_plan', 'workout_sessions', 'training_plans', ['plan_id'], ['id'], ondelete='RESTRICT')
    op.create_check_constraint('ck_workout_sessions_fatigue_range', 'workout_sessions', 'fatigue_level BETWEEN 1 AND 10')
    op.create_check_constraint('ck_workout_sessions_notes_length', 'workout_sessions', 'notes IS NULL OR char_length(notes) <= 1000')
    op.create_check_constraint('ck_workout_sessions_pain_range', 'workout_sessions', 'pain_level BETWEEN 0 AND 10')
    op.create_check_constraint('ck_workout_sessions_plan_day_range', 'workout_sessions', 'plan_day_index BETWEEN 1 AND 7')
    op.create_check_constraint('ck_workout_sessions_sets_nonempty_array', 'workout_sessions', "\n            jsonb_typeof(sets_data) = 'array'\n            AND jsonb_array_length(sets_data) >= 1\n            ")
    


def downgrade() -> None:
    """
    移除核心业务表的检查约束、唯一约束、部分唯一索引和外键。

    :return: 无返回值。
    """
    op.drop_constraint('ck_workout_sessions_sets_nonempty_array', 'workout_sessions', type_='check')
    op.drop_constraint('ck_workout_sessions_plan_day_range', 'workout_sessions', type_='check')
    op.drop_constraint('ck_workout_sessions_pain_range', 'workout_sessions', type_='check')
    op.drop_constraint('ck_workout_sessions_notes_length', 'workout_sessions', type_='check')
    op.drop_constraint('ck_workout_sessions_fatigue_range', 'workout_sessions', type_='check')
    op.drop_constraint('fk_workout_sessions_plan', 'workout_sessions', type_='foreignkey')
    op.drop_constraint('ck_user_memories_type_allowed', 'user_memories', type_='check')
    op.drop_constraint('ck_user_memories_status_allowed', 'user_memories', type_='check')
    op.drop_constraint('ck_user_memories_source_allowed', 'user_memories', type_='check')
    op.drop_constraint('ck_user_memories_content_length', 'user_memories', type_='check')
    op.drop_constraint('ck_training_plans_week_range', 'training_plans', type_='check')
    op.drop_constraint('ck_training_plans_version_positive', 'training_plans', type_='check')
    op.drop_constraint('ck_training_plans_status_allowed', 'training_plans', type_='check')
    op.drop_constraint('fk_training_plans_source_proposal', 'training_plans', type_='foreignkey')
    op.drop_constraint('uq_training_plans_user_week_version', 'training_plans', type_='unique')
    op.drop_index('uq_training_plans_user_week_current', table_name='training_plans', postgresql_where=sa.text("status IN ('scheduled', 'active')"))
    op.drop_constraint('uq_training_plans_source_proposal', 'training_plans', type_='unique')
    op.drop_constraint('ck_plan_proposals_type_allowed', 'training_plan_proposals', type_='check')
    op.drop_constraint('ck_plan_proposals_status_allowed', 'training_plan_proposals', type_='check')
    op.drop_constraint('ck_plan_proposals_revision_positive', 'training_plan_proposals', type_='check')
    op.drop_constraint('ck_plan_proposals_operation_allowed', 'training_plan_proposals', type_='check')
    op.drop_constraint('fk_plan_proposals_approved_plan', 'training_plan_proposals', type_='foreignkey')
    op.drop_constraint('fk_plan_proposals_parent', 'training_plan_proposals', type_='foreignkey')
    op.drop_constraint('fk_plan_proposals_base_plan', 'training_plan_proposals', type_='foreignkey')
    op.drop_index('uq_plan_proposals_user_week_pending', table_name='training_plan_proposals', postgresql_where=sa.text("status IN ('pending', 'approving')"))
    op.drop_constraint('uq_plan_proposals_user_parent_revision', 'training_plan_proposals', type_='unique')
    op.drop_constraint('uq_plan_proposals_approved_plan', 'training_plan_proposals', type_='unique')
    op.drop_constraint('ck_fitness_profiles_weight_range', 'fitness_profiles', type_='check')
    op.drop_constraint('ck_fitness_profiles_sex_allowed', 'fitness_profiles', type_='check')
    op.drop_constraint('ck_fitness_profiles_sessions_range', 'fitness_profiles', type_='check')
    op.drop_constraint('ck_fitness_profiles_session_minutes_range', 'fitness_profiles', type_='check')
    op.drop_constraint('ck_fitness_profiles_height_range', 'fitness_profiles', type_='check')
    op.drop_constraint('ck_fitness_profiles_goal_allowed', 'fitness_profiles', type_='check')
    op.drop_constraint('ck_fitness_profiles_age_range', 'fitness_profiles', type_='check')
