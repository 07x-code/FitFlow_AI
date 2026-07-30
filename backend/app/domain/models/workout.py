from pydantic import BaseModel, Field


class WorkoutSetLog(BaseModel):
    """训练记录中的单组动作数据。"""

    exercise_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    exercise_name: str = Field(min_length=1)
    set_number: int = Field(ge=1, le=20)
    weight_kg: float = Field(ge=0, le=500)
    reps: int = Field(ge=0, le=100)
    rpe: float = Field(ge=1, le=10)


class WorkoutSafetyAlert(BaseModel):
    """根据训练反馈生成的安全提醒。"""

    level: str
    message: str


class WorkoutSessionCreate(BaseModel):
    """创建训练记录的输入。"""

    plan_day_index: int = Field(default=1, ge=1, le=7)
    completed: bool
    fatigue_level: int = Field(ge=1, le=10)
    pain_level: int = Field(ge=0, le=10)
    notes: str | None = Field(default=None, max_length=1000)
    sets: list[WorkoutSetLog] = Field(min_length=1)


class WorkoutSessionResponse(BaseModel):
    """已保存的训练记录响应。"""

    id: int
    plan_id: int
    plan_day_index: int
    plan_day_name: str
    completed: bool
    fatigue_level: int
    pain_level: int
    notes: str | None = None
    sets: list[WorkoutSetLog]
    safety_alert: WorkoutSafetyAlert | None = None
    created_at: str


class WorkoutHistoryResponse(BaseModel):
    """用户训练历史响应。"""

    sessions: list[WorkoutSessionResponse]
