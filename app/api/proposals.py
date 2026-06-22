from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.domain.models import (
    ProposalDecision,
    ProposalDecisionRequest,
    ProposalListResponse,
    ProposalStatus,
    SafetyCheckResult,
    TrainingPlanProposalResponse,
)
from app.domain.plan_generator import generate_beginner_plan
from app.domain.risk_rules import assess_risk
from app.domain.training_rules import validate_beginner_plan
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.proposal_repository import TrainingPlanProposalRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository


router = APIRouter(prefix="/api/proposals", tags=["proposals"])

profile_repository = ProfileRepository()
proposal_repository = TrainingPlanProposalRepository()
training_plan_repository = TrainingPlanRepository()


@router.post(
    "/training-plan",
    response_model=TrainingPlanProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_training_plan_proposal(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanProposalResponse:
    profile = profile_repository.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    risk = assess_risk(profile)
    if risk["can_auto_plan"] is False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Automatic plan generation is blocked.",
                "risk": risk,
            },
        )

    plan = generate_beginner_plan(profile)
    safety_check = SafetyCheckResult.model_validate(validate_beginner_plan(plan))
    if safety_check.valid is False:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Generated proposal failed safety check.",
                "safety_check": safety_check.model_dump(),
            },
        )

    return proposal_repository.create(user_id, plan, safety_check)


@router.get("", response_model=ProposalListResponse)
def list_proposals(
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> ProposalListResponse:
    return ProposalListResponse(
        proposals=proposal_repository.list_by_user(user_id),
    )


@router.get("/{proposal_id}", response_model=TrainingPlanProposalResponse)
def get_proposal(
    proposal_id: int,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanProposalResponse:
    proposal = proposal_repository.get_by_id_for_user(user_id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    return proposal


@router.post("/{proposal_id}/decision", response_model=TrainingPlanProposalResponse)
def decide_proposal(
    proposal_id: int,
    request: ProposalDecisionRequest,
    user_id: Annotated[str, Header(alias="X-User-ID")],
) -> TrainingPlanProposalResponse:
    proposal = proposal_repository.get_by_id_for_user(user_id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Proposal has already been decided.",
        )

    if request.decision == ProposalDecision.APPROVE:
        approved_plan = training_plan_repository.save(
            user_id,
            proposal.plan,
            proposal.safety_check,
        )
        updated_proposal = proposal_repository.approve(
            user_id=user_id,
            proposal_id=proposal_id,
            approved_plan_id=approved_plan.id,
            decision_note=request.decision_note,
        )
    else:
        updated_proposal = proposal_repository.reject(
            user_id=user_id,
            proposal_id=proposal_id,
            decision_note=request.decision_note,
        )

    if updated_proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    return updated_proposal
