from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import get_profile_use_cases
from app.application.use_cases.profiles import ProfileUseCases
from app.domain.models import FitnessProfileCreate, ProfileAssessmentResponse


router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("", response_model=ProfileAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile: FitnessProfileCreate,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProfileUseCases, Depends(get_profile_use_cases)],
) -> ProfileAssessmentResponse:
    """
    创建或更新当前用户的健身画像。

    :param profile: 待保存的健身画像。
    :param user_id: 当前用户标识。
    :param use_cases: 用户画像应用用例。
    :return: 用户画像评估结果。
    """
    return await use_cases.create(user_id, profile) 


@router.get("/me", response_model=ProfileAssessmentResponse)
async def get_my_profile(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProfileUseCases, Depends(get_profile_use_cases)],
) -> ProfileAssessmentResponse:
    """
    查询当前用户的健身画像。

    :param user_id: 当前用户标识。
    :param use_cases: 用户画像应用用例。
    :return: 用户画像评估结果。
    """
    return await use_cases.get(user_id)
