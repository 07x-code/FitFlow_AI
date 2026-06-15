from pydantic import BaseModel, Field


class FitnessProfileCreate(BaseModel):
    age: int = Field(ge=16, le=80)
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=35, le=250)
    goal: str
    sessions_per_week: int = Field(ge=2, le=4)
    session_minutes: int = Field(ge=30, le=120)