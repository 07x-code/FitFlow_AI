from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.persistence.postgres.base import Base
from app.infrastructure.persistence.postgres.models import (
    FitnessProfileRecord,
    UserMemoryRecord,
    TrainingPlanRecord,
    TrainingPlanProposalRecord,
    WorkoutSessionRecord,
)


def test_fitness_profile_table_metadata():
    """
    验证用户健身画像表的基础字段和主键配置。

    :return: 无返回值。
    """
    table = Base.metadata.tables["fitness_profiles"]

    assert FitnessProfileRecord.__table__ is table
    assert set(table.columns.keys()) == {
        "user_id",
        "age",
        "sex",
        "height_cm",
        "weight_kg",
        "goal",
        "sessions_per_week",
        "session_minutes",
        "health_flags",
        "created_at",
        "updated_at",
    }
    assert table.c.user_id.primary_key is True
    assert isinstance(table.c.health_flags.type, JSONB)

def test_user_memory_table_metadata():
    """
    验证长期记忆表包含确认状态和审计字段。

    :return: 无返回值。
    """
    table = Base.metadata.tables["user_memories"]

    assert UserMemoryRecord.__table__ is table
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "memory_type",
        "content",
        "source",
        "status",
        "confirmed_at",
        "created_at",
        "updated_at",
    }
    assert table.c.id.primary_key is True
    assert table.c.user_id.nullable is False
    assert table.c.content.nullable is False
    assert table.c.confirmed_at.nullable is True

    #长期记忆索引
    index_columns = {
        tuple(column.name for column in index.columns)
        for index in table.indexes
    }
    
    assert ("user_id", "status", "id") in index_columns


def test_training_plan_table_metadata():
    """
    验证正式训练计划表包含自然周、版本和来源字段。

    :return: 无返回值。
    """
    table = Base.metadata.tables["training_plans"]

    assert TrainingPlanRecord.__table__ is table
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "week_start",
        "week_end",
        "timezone",
        "version",
        "status",
        "source_proposal_id",
        "plan_data",
        "safety_check",
        "created_at",
        "activated_at",
    }
    assert table.c.id.primary_key is True
    assert table.c.source_proposal_id.nullable is False
    assert isinstance(table.c.plan_data.type, JSONB)
    assert isinstance(table.c.safety_check.type, JSONB)
    index_columns = {
        tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert ("user_id", "week_start") in index_columns
    assert ("user_id", "status", "week_start") in index_columns

def test_training_plan_proposal_table_metadata():
    """
    验证训练计划提案表包含修订、审批和追溯字段。

    :return: 无返回值。
    """
    table = Base.metadata.tables["training_plan_proposals"]

    assert TrainingPlanProposalRecord.__table__ is table
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "proposal_type",
        "operation",
        "target_week_start",
        "base_plan_id",
        "parent_proposal_id",
        "revision",
        "status",
        "plan_snapshot",
        "safety_check",
        "generation_summary",
        "approved_plan_id",
        "decision_note",
        "created_at",
        "decided_at",
    }
    assert table.c.id.primary_key is True
    assert table.c.target_week_start.nullable is False
    assert table.c.base_plan_id.nullable is True
    assert table.c.parent_proposal_id.nullable is True
    assert table.c.approved_plan_id.nullable is True
    assert isinstance(table.c.plan_snapshot.type, JSONB)
    assert isinstance(table.c.safety_check.type, JSONB)

    index_columns = {
        tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert (
        "user_id",
        "target_week_start",
        "status",
    ) in index_columns
    assert (
        "user_id",
        "parent_proposal_id",
        "revision",
    ) in index_columns




def test_workout_session_table_metadata():
    """
    验证训练记录表包含计划定位、反馈和训练组数据。

    :return: 无返回值。
    """
    table = Base.metadata.tables["workout_sessions"]

    assert WorkoutSessionRecord.__table__ is table
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "plan_id",
        "plan_day_index",
        "plan_day_name",
        "completed",
        "fatigue_level",
        "pain_level",
        "notes",
        "sets_data",
        "safety_alert",
        "created_at",
    }
    assert table.c.id.primary_key is True
    assert table.c.plan_id.nullable is False
    assert table.c.completed.nullable is False
    assert table.c.notes.nullable is True
    assert isinstance(table.c.sets_data.type, JSONB)
    assert isinstance(table.c.safety_alert.type, JSONB)

    index_columns = {
        tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert ("user_id", "created_at") in index_columns
    assert (
        "user_id",
        "plan_id",
        "created_at",
    ) in index_columns


    