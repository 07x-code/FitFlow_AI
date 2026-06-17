from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FitnessGoal(StrEnum): #训练目标
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    GENERAL_FITNESS = "general_fitness"


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class FitnessProfileCreate(BaseModel):  #健身档案创建
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=16, le=80)
    sex: Sex
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=35, le=250)
    goal: FitnessGoal
    sessions_per_week: int = Field(ge=2, le=4)
    session_minutes: int = Field(ge=30, le=120)
    health_flags: list[str] = Field(default_factory=list)


class ExercisePrescription(BaseModel):  #运动处方
    exercise_name: str = Field(min_length=1)
    sets: int = Field(ge=1, le=5)
    reps_min: int = Field(ge=1, le=30)
    reps_max: int = Field(ge=1, le=30)
    target_rpe: float = Field(ge=1, le=10)


class WorkoutDayDraft(BaseModel):  #
    name: str = Field(min_length=1)
    exercises: list[ExercisePrescription] = Field(min_length=1)


class TrainingPlanDraft(BaseModel):
    days: list[WorkoutDayDraft] = Field(min_length=1)



#以下是回应数据格式
class RiskAssessment(BaseModel):
    level: str
    can_auto_plan: bool


class NutritionTargets(BaseModel):
    bmr_kcal: int
    calorie_target_kcal: int
    protein_target_g: int


class ProfileAssessmentResponse(BaseModel):
    profile: FitnessProfileCreate
    risk: RiskAssessment
    nutrition: NutritionTargets
