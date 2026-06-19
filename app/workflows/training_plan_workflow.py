from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.domain.models import (
    FitnessProfileCreate,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanDraftResponse,
    TrainingPlanHistoryItem,
)
from app.domain.plan_generator import generate_beginner_plan
from app.domain.risk_rules import assess_risk
from app.domain.training_rules import validate_beginner_plan
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository


class TrainingPlanWorkflowState(TypedDict, total=False):
    user_id: str
    profile: FitnessProfileCreate
    risk: dict[str, str | bool]
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    saved_plan: TrainingPlanHistoryItem
    error_status_code: int
    error_detail: Any


@dataclass(frozen=True)
class TrainingPlanWorkflowResult:
    status_code: int
    response: TrainingPlanDraftResponse | None = None
    error_detail: Any = None


class TrainingPlanWorkflow:
    def __init__(
        self,
        profile_repository: ProfileRepository,
        training_plan_repository: TrainingPlanRepository,
    ) -> None:
        self.profile_repository = profile_repository
        self.training_plan_repository = training_plan_repository
        self.graph = self._build_graph()

    def run(self, user_id: str) -> TrainingPlanWorkflowResult:
        final_state = self.graph.invoke({"user_id": user_id})

        if "error_status_code" in final_state:
            return TrainingPlanWorkflowResult(
                status_code=final_state["error_status_code"],
                error_detail=final_state["error_detail"],
            )

        return TrainingPlanWorkflowResult(
            status_code=HTTPStatus.CREATED,
            response=TrainingPlanDraftResponse(
                plan=final_state["plan"],
                safety_check=final_state["safety_check"],
            ),
        )

    def _build_graph(self):
        workflow = StateGraph(TrainingPlanWorkflowState)

        workflow.add_node("load_profile", self._load_profile)
        workflow.add_node("assess_risk", self._assess_risk)
        workflow.add_node("block_automatic_planning", self._block_automatic_planning)
        workflow.add_node("generate_plan", self._generate_plan)
        workflow.add_node("validate_plan", self._validate_plan)
        workflow.add_node("reject_unsafe_plan", self._reject_unsafe_plan)
        workflow.add_node("save_plan", self._save_plan)

        workflow.add_edge(START, "load_profile")
        workflow.add_conditional_edges(
            "load_profile",
            self._route_after_profile,
            {
                "profile_found": "assess_risk",
                "missing_profile": END,
            },
        )
        workflow.add_conditional_edges(
            "assess_risk",
            self._route_after_risk,
            {
                "safe_to_plan": "generate_plan",
                "blocked": "block_automatic_planning",
            },
        )
        workflow.add_edge("block_automatic_planning", END)
        workflow.add_edge("generate_plan", "validate_plan")
        workflow.add_conditional_edges(
            "validate_plan",
            self._route_after_safety_check,
            {
                "safe_plan": "save_plan",
                "unsafe_plan": "reject_unsafe_plan",
            },
        )
        workflow.add_edge("reject_unsafe_plan", END)
        workflow.add_edge("save_plan", END)

        return workflow.compile()

    def _load_profile(
        self,
        state: TrainingPlanWorkflowState,
    ) -> TrainingPlanWorkflowState:
        profile = self.profile_repository.get(state["user_id"])
        if profile is None:
            return {
                "error_status_code": HTTPStatus.NOT_FOUND,
                "error_detail": "Profile not found.",
            }

        return {"profile": profile}

    def _route_after_profile(
        self,
        state: TrainingPlanWorkflowState,
    ) -> Literal["profile_found", "missing_profile"]:
        if "error_status_code" in state:
            return "missing_profile"

        return "profile_found"

    def _assess_risk(
        self,
        state: TrainingPlanWorkflowState,
    ) -> TrainingPlanWorkflowState:
        return {"risk": assess_risk(state["profile"])}

    def _route_after_risk(
        self,
        state: TrainingPlanWorkflowState,
    ) -> Literal["safe_to_plan", "blocked"]:
        if state["risk"]["can_auto_plan"] is False:
            return "blocked"

        return "safe_to_plan"

    def _block_automatic_planning(
        self,
        state: TrainingPlanWorkflowState,
    ) -> TrainingPlanWorkflowState:
        return {
            "error_status_code": HTTPStatus.CONFLICT,
            "error_detail": {
                "message": "Automatic plan generation is blocked.",
                "risk": state["risk"],
            },
        }

    def _generate_plan(
        self,
        state: TrainingPlanWorkflowState,
    ) -> TrainingPlanWorkflowState:
        return {"plan": generate_beginner_plan(state["profile"])}

    def _validate_plan(
        self,
        state: TrainingPlanWorkflowState,
    ) -> TrainingPlanWorkflowState:
        return {
            "safety_check": SafetyCheckResult.model_validate(
                validate_beginner_plan(state["plan"])
            )
        }

    def _route_after_safety_check(
        self,
        state: TrainingPlanWorkflowState,
    ) -> Literal["safe_plan", "unsafe_plan"]:
        if state["safety_check"].valid is False:
            return "unsafe_plan"

        return "safe_plan"

    def _reject_unsafe_plan(
        self,
        state: TrainingPlanWorkflowState,
    ) -> TrainingPlanWorkflowState:
        return {
            "error_status_code": HTTPStatus.UNPROCESSABLE_ENTITY,
            "error_detail": {
                "message": "Generated plan failed safety check.",
                "safety_check": state["safety_check"].model_dump(),
            },
        }

    def _save_plan(
        self,
        state: TrainingPlanWorkflowState,
    ) -> TrainingPlanWorkflowState:
        saved_plan = self.training_plan_repository.save(
            state["user_id"],
            state["plan"],
            state["safety_check"],
        )
        return {"saved_plan": saved_plan}


def create_training_plan_workflow(
    profile_repository: ProfileRepository,
    training_plan_repository: TrainingPlanRepository,
) -> TrainingPlanWorkflow:
    return TrainingPlanWorkflow(
        profile_repository=profile_repository,
        training_plan_repository=training_plan_repository,
    )
