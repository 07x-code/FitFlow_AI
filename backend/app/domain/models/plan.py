from datetime import date, timedelta
from enum import StrEnum
from typing import Self
from pydantic import BaseModel, Field, model_validator


class ExercisePrescription(BaseModel):
    """训练计划中的单个动作处方。"""

    exercise_name: str = Field(min_length=1)
    sets: int = Field(ge=1, le=5)
    reps_min: int = Field(ge=1, le=30)
    reps_max: int = Field(ge=1, le=30)
    target_rpe: float = Field(ge=1, le=10)


class WorkoutDayDraft(BaseModel):
    """训练计划中的单个训练日。"""

    scheduled_date: date
    name: str = Field(min_length=1)
    focus: str = Field(min_length=1, max_length=200)
    estimated_minutes: int = Field(ge=30, le=120)
    exercises: list[ExercisePrescription] = Field(min_length=1)


class TrainingPlanDraft(BaseModel):
    """尚未成为正式记录的训练计划草案。"""

    week_start: date
    week_end: date
    timezone: str = Field(min_length=1, max_length=64)
    goal_summary: str = Field(min_length=1, max_length=500)
    days: list[WorkoutDayDraft] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_week_range(self) -> Self:
        """
        验证计划的结束日期与开始日期构成完整自然周。

        :return: 周范围校验通过的训练计划草案。
        """
        expected_week_end = self.week_start + timedelta(days=6)
        if self.week_end != expected_week_end:
            raise ValueError(
                "week_end 必须是 week_start 之后的第 6 天。"
            )

        return self


class SafetyCheckResult(BaseModel):
    """训练计划的确定性安全检查结果。"""

    valid: bool
    violations: list[dict[str, str]]


class TrainingPlanDraftResponse(BaseModel):
    """训练计划草案及其安全检查响应。"""

    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult


class TrainingPlanStatus(StrEnum):
    """正式训练计划状态。"""

    SCHEDULED = "scheduled"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    COMPLETED = "completed"


class TrainingPlanHistoryItem(BaseModel):
    """已持久化的训练计划记录。"""

    id: int
    version: int = Field(ge=1)
    status: TrainingPlanStatus
    source_proposal_id: int = Field(gt=0)
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    created_at: str


class TrainingPlanHistoryResponse(BaseModel):
    """用户训练计划历史响应。"""

    plans: list[TrainingPlanHistoryItem]


class TrainingPlanExplanationResponse(BaseModel):
    """训练计划解释响应。"""

    plan_id: int
    summary: str
    reasons: list[str]
    safety_notes: list[str]
