from fastapi import APIRouter

from app.domain.models import FitnessProfileCreate
from app.domain.nutrition_rules import calculate_nutrition_targets
from app.domain.risk_rules import assess_risk


router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("", status_code=201)
def create_profile(profile: FitnessProfileCreate) -> dict:
    return {
        "profile": profile.model_dump(mode="json"),
        "risk": assess_risk(profile),
        "nutrition": calculate_nutrition_targets(profile),
    }
