from enum import StrEnum

from pydantic import BaseModel, Field


class FitnessGoal(StrEnum):
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    GENERAL_FITNESS = "general_fitness"

class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"

class FitnessProfileCreate(BaseModel):
    age: int = Field(ge=16, le=80)
    sex: Sex
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=35, le=250)
    goal: FitnessGoal
    sessions_per_week: int = Field(ge=2, le=4)
    session_minutes: int = Field(ge=30, le=120)