from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.domain.models import FitnessProfileCreate, ProfileAssessmentResponse
from app.domain.nutrition_rules import calculate_nutrition_targets
from app.domain.risk_rules import assess_risk
from app.infrastructure.profile_repository import ProfileRepository


router = APIRouter(prefix="/api/profiles", tags=["profiles"])

profile_repository = ProfileRepository()


def build_profile_assessment(profile: FitnessProfileCreate) -> ProfileAssessmentResponse:
    return ProfileAssessmentResponse(
        profile=profile,
        risk=assess_risk(profile),
        nutrition=calculate_nutrition_targets(profile),
    )


@router.post("", response_model=ProfileAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile: FitnessProfileCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> ProfileAssessmentResponse:
    profile_repository.save(user_id, profile)
    return build_profile_assessment(profile)


@router.get("/me", response_model=ProfileAssessmentResponse)
def get_my_profile(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> ProfileAssessmentResponse:
    profile = profile_repository.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return build_profile_assessment(profile)
