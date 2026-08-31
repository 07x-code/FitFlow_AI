from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import get_proposal_use_cases
from app.application.use_cases.proposals import ProposalUseCases
from app.domain.models import (
    ProposalDecisionRequest,
    ProposalListResponse,
    ProposalRevisionRequest,
    TrainingPlanProposalResponse,
)


router = APIRouter(prefix="/api/proposals", tags=["proposals"])


@router.post(
    "/training-plan",
    response_model=TrainingPlanProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_training_plan_proposal(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProposalUseCases, Depends(get_proposal_use_cases)],
) -> TrainingPlanProposalResponse:
    return await use_cases.create_training_plan(user_id)


@router.get("", response_model=ProposalListResponse)
async def list_proposals(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProposalUseCases, Depends(get_proposal_use_cases)],
) -> ProposalListResponse:
    return await use_cases.list(user_id)


@router.get("/{proposal_id}", response_model=TrainingPlanProposalResponse)
async def get_proposal(
    proposal_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProposalUseCases, Depends(get_proposal_use_cases)],
) -> TrainingPlanProposalResponse:
    return await use_cases.get(user_id, proposal_id)


@router.post("/{proposal_id}/decision", response_model=TrainingPlanProposalResponse)
async def decide_proposal(
    proposal_id: int,
    request: ProposalDecisionRequest,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProposalUseCases, Depends(get_proposal_use_cases)],
) -> TrainingPlanProposalResponse:
    return await use_cases.decide(user_id, proposal_id, request)


@router.post(
    "/{proposal_id}/revisions",
    response_model=TrainingPlanProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def revise_proposal(
    proposal_id: int,
    request: ProposalRevisionRequest,
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ProposalUseCases, Depends(get_proposal_use_cases)],
) -> TrainingPlanProposalResponse:
    """
    根据用户反馈生成新版本训练计划提案。

    :param proposal_id: 待修改的提案标识。
    :param request: 用户提交的修改意见。
    :param user_id: 用户标识。
    :param use_cases: Proposal 应用用例。
    :return: 等待用户确认的新版本提案。
    """
    return await use_cases.revise(user_id, proposal_id, request)
