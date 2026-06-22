from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FitnessGoal(StrEnum):
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    GENERAL_FITNESS = "general_fitness"


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class FitnessProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=16, le=80)
    sex: Sex
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=35, le=250)
    goal: FitnessGoal
    sessions_per_week: int = Field(ge=2, le=4)
    session_minutes: int = Field(ge=30, le=120)
    health_flags: list[str] = Field(default_factory=list)


class ExercisePrescription(BaseModel):
    exercise_name: str = Field(min_length=1)
    sets: int = Field(ge=1, le=5)
    reps_min: int = Field(ge=1, le=30)
    reps_max: int = Field(ge=1, le=30)
    target_rpe: float = Field(ge=1, le=10)


class WorkoutDayDraft(BaseModel):
    name: str = Field(min_length=1)
    exercises: list[ExercisePrescription] = Field(min_length=1)


class TrainingPlanDraft(BaseModel):
    days: list[WorkoutDayDraft] = Field(min_length=1)


class SafetyCheckResult(BaseModel):
    valid: bool
    violations: list[dict[str, str]]


class TrainingPlanDraftResponse(BaseModel):
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult


class TrainingPlanHistoryItem(BaseModel):
    id: int
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    created_at: str


class TrainingPlanHistoryResponse(BaseModel):
    plans: list[TrainingPlanHistoryItem]


class TrainingPlanExplanationResponse(BaseModel):
    plan_id: int
    summary: str
    reasons: list[str]
    safety_notes: list[str]


class ProposalType(StrEnum):
    TRAINING_PLAN = "training_plan"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProposalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ProposalDecisionRequest(BaseModel):
    decision: ProposalDecision
    decision_note: str | None = Field(default=None, max_length=500)


class TrainingPlanProposalResponse(BaseModel):
    id: int
    type: ProposalType
    status: ProposalStatus
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    approved_plan_id: int | None = None
    decision_note: str | None = None
    created_at: str
    decided_at: str | None = None


class ProposalListResponse(BaseModel):
    proposals: list[TrainingPlanProposalResponse]

class CoachChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class CoachChatResponse(BaseModel):
    answer: str
    safety_level: str
    referenced_plan_id: int | None = None


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
