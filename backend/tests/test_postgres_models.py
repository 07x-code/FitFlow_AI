from sqlalchemy import CheckConstraint, UniqueConstraint
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

    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert check_names == {
        "ck_fitness_profiles_age_range",
        "ck_fitness_profiles_sex_allowed",
        "ck_fitness_profiles_height_range",
        "ck_fitness_profiles_weight_range",
        "ck_fitness_profiles_goal_allowed",
        "ck_fitness_profiles_sessions_range",
        "ck_fitness_profiles_session_minutes_range",
    }

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

    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert check_names == {
        "ck_user_memories_type_allowed",
        "ck_user_memories_source_allowed",
        "ck_user_memories_status_allowed",
        "ck_user_memories_content_length",
    }


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

    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    unique_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert check_names == {
        "ck_training_plans_week_range",
        "ck_training_plans_version_positive",
        "ck_training_plans_status_allowed",
    }
    assert "uq_training_plans_user_week_version" in unique_names
    assert "uq_training_plans_source_proposal" in unique_names



    current_plan_index = next(
        index
        for index in table.indexes
        if index.name == "uq_training_plans_user_week_current"
    )

    assert current_plan_index.unique is True
    assert tuple(
        column.name for column in current_plan_index.columns
    ) == (
        "user_id",
        "week_start",
    )

    where_clause = current_plan_index.dialect_options["postgresql"]["where"]

    assert where_clause is not None
    assert "scheduled" in str(where_clause)
    assert "active" in str(where_clause)


    source_foreign_key = next(
        iter(table.c.source_proposal_id.foreign_keys)
    )

    assert (
        source_foreign_key.target_fullname
        == "training_plan_proposals.id"
    )
    assert source_foreign_key.ondelete == "RESTRICT"
    assert (
        source_foreign_key.name
        == "fk_training_plans_source_proposal"
    )
    assert source_foreign_key.use_alter is True

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

    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    unique_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert check_names == {
        "ck_plan_proposals_type_allowed",
        "ck_plan_proposals_operation_allowed",
        "ck_plan_proposals_status_allowed",
        "ck_plan_proposals_revision_positive",
    }
    assert "uq_plan_proposals_user_parent_revision" in unique_names
    assert "uq_plan_proposals_approved_plan" in unique_names



    #同一用户同一周最多一个待处理 Proposal”的部分唯一索引
    pending_proposal_index = next(
        index
        for index in table.indexes
        if index.name == "uq_plan_proposals_user_week_pending"
    )

    assert pending_proposal_index.unique is True
    assert tuple(
        column.name for column in pending_proposal_index.columns
    ) == (
        "user_id",
        "target_week_start",
    )

    where_clause = pending_proposal_index.dialect_options[
        "postgresql"
    ]["where"]

    assert where_clause is not None
    assert "pending" in str(where_clause)
    assert "approving" in str(where_clause)

    #外键测试
    base_plan_foreign_key = next(
        iter(table.c.base_plan_id.foreign_keys)
    )
    parent_proposal_foreign_key = next(
        iter(table.c.parent_proposal_id.foreign_keys)
    )
    approved_plan_foreign_key = next(
        iter(table.c.approved_plan_id.foreign_keys)
    )

    assert (
        base_plan_foreign_key.target_fullname
        == "training_plans.id"
    )
    assert base_plan_foreign_key.ondelete == "RESTRICT"
    assert (
        base_plan_foreign_key.name
        == "fk_plan_proposals_base_plan"
    )

    assert (
        parent_proposal_foreign_key.target_fullname
        == "training_plan_proposals.id"
    )
    assert parent_proposal_foreign_key.ondelete == "RESTRICT"
    assert (
        parent_proposal_foreign_key.name
        == "fk_plan_proposals_parent"
    )

    assert (
        approved_plan_foreign_key.target_fullname
        == "training_plans.id"
    )
    assert approved_plan_foreign_key.ondelete == "RESTRICT"
    assert (
        approved_plan_foreign_key.name
        == "fk_plan_proposals_approved_plan"
    )




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

    #训练记录添加训练日、疲劳和疼痛范围约束
    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert check_names == {
        "ck_workout_sessions_plan_day_range",
        "ck_workout_sessions_fatigue_range",
        "ck_workout_sessions_pain_range",
        "ck_workout_sessions_notes_length",
        "ck_workout_sessions_sets_nonempty_array",
    }


    #外键测试
    plan_foreign_key = next(
        iter(table.c.plan_id.foreign_keys)
    )

    assert plan_foreign_key.target_fullname == "training_plans.id"
    assert plan_foreign_key.ondelete == "RESTRICT"
    assert (
        plan_foreign_key.name
        == "fk_workout_sessions_plan"
    )
    