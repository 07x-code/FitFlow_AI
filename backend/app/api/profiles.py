from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import get_profile_use_cases
from app.application.use_cases.profiles import ProfileUseCases
from app.domain.models import FitnessProfileCreate, ProfileAssessmentResponse


router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("", response_model=ProfileAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile: FitnessProfileCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProfileUseCases, Depends(get_profile_use_cases)],
) -> ProfileAssessmentResponse:
    return use_cases.create(user_id, profile)


@router.get("/me", response_model=ProfileAssessmentResponse)
def get_my_profile(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProfileUseCases, Depends(get_profile_use_cases)],
) -> ProfileAssessmentResponse:
    return use_cases.get(user_id)
