from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FitnessGoal(StrEnum):
    """用户健身目标。"""

    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    GENERAL_FITNESS = "general_fitness"


class Sex(StrEnum):
    """用户生理性别。"""

    MALE = "male"
    FEMALE = "female"


class FitnessProfileCreate(BaseModel):
    """创建或更新用户健身画像的输入。"""

    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=16, le=80)
    sex: Sex
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=35, le=250)
    goal: FitnessGoal
    sessions_per_week: int = Field(ge=2, le=4)
    session_minutes: int = Field(ge=30, le=120)
    health_flags: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """用户健康风险评估。"""

    level: str
    can_auto_plan: bool


class NutritionTargets(BaseModel):
    """根据用户画像计算出的营养目标。"""

    bmr_kcal: int
    calorie_target_kcal: int
    protein_target_g: int


class ProfileAssessmentResponse(BaseModel):
    """用户画像、风险与营养评估的组合响应。"""

    profile: FitnessProfileCreate
    risk: RiskAssessment
    nutrition: NutritionTargets
