from pydantic import BaseModel, Field


class ExercisePrescription(BaseModel):
    """训练计划中的单个动作处方。"""

    exercise_name: str = Field(min_length=1)
    sets: int = Field(ge=1, le=5)
    reps_min: int = Field(ge=1, le=30)
    reps_max: int = Field(ge=1, le=30)
    target_rpe: float = Field(ge=1, le=10)


class WorkoutDayDraft(BaseModel):
    """训练计划中的单个训练日。"""

    name: str = Field(min_length=1)
    exercises: list[ExercisePrescription] = Field(min_length=1)


class TrainingPlanDraft(BaseModel):
    """尚未成为正式记录的训练计划草案。"""

    days: list[WorkoutDayDraft] = Field(min_length=1)


class SafetyCheckResult(BaseModel):
    """训练计划的确定性安全检查结果。"""

    valid: bool
    violations: list[dict[str, str]]


class TrainingPlanDraftResponse(BaseModel):
    """训练计划草案及其安全检查响应。"""

    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult


class TrainingPlanHistoryItem(BaseModel):
    """已持久化的训练计划记录。"""

    id: int
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
