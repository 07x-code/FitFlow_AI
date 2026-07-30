from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from app.ai.core import Agent
from app.ai.tools.fitness import (
    ASSESS_RISK_TOOL,
    GENERATE_TRAINING_PLAN_TOOL,
    GET_PROFILE_TOOL,
    SAVE_TRAINING_PLAN_TOOL,
    VALIDATE_TRAINING_PLAN_TOOL,
    SaveTrainingPlanInput,
    create_training_plan_tool_registry,
)
from app.ai.tools.registry import ToolRegistry
from app.domain.models import (
    FitnessProfileCreate,
    RiskAssessment,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanDraftResponse,
    TrainingPlanHistoryItem,
)
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanRepositoryPort,
)


class TrainingPlanAgentState(TypedDict, total=False):
    user_id: str
    profile: FitnessProfileCreate
    risk: RiskAssessment
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    saved_plan: TrainingPlanHistoryItem
    error_status_code: int
    error_detail: Any


@dataclass(frozen=True)
class TrainingPlanAgentResult:
    status_code: int
    response: TrainingPlanDraftResponse | None = None
    error_detail: Any = None


class TrainingPlanAgent(Agent[str, TrainingPlanAgentResult]):
    """带有确定性安全门禁的规划与求解 Agent。

    LangGraph 负责流程编排，同时每项领域能力都通过统一工具注册中心暴露，
    该注册中心也供对话 Agent 使用。
    """

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
    ) -> None:
        super().__init__(
            name="training-plan-agent",
            system_prompt=(
                "Create beginner plans only after profile and risk checks, "
                "validate every plan, and persist only safe results."
            ),
        )
        self.tool_registry = tool_registry
        self.graph = self._build_graph()

    def run(
        self,
        agent_input: str,
        **kwargs: object,
    ) -> TrainingPlanAgentResult:
        final_state = self.graph.invoke({"user_id": agent_input})

        if "error_status_code" in final_state:
            return TrainingPlanAgentResult(
                status_code=final_state["error_status_code"],
                error_detail=final_state["error_detail"],
            )

        return TrainingPlanAgentResult(
            status_code=HTTPStatus.CREATED,
            response=TrainingPlanDraftResponse(
                plan=final_state["plan"],
                safety_check=final_state["safety_check"],
            ),
        )

    def _build_graph(self):
        workflow = StateGraph(TrainingPlanAgentState)

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
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        profile = cast(
            FitnessProfileCreate | None,
            self.tool_registry.execute(GET_PROFILE_TOOL, state["user_id"]),
        )
        if profile is None:
            return {
                "error_status_code": HTTPStatus.NOT_FOUND,
                "error_detail": "Profile not found.",
            }

        return {"profile": profile}

    @staticmethod
    def _route_after_profile(
        state: TrainingPlanAgentState,
    ) -> Literal["profile_found", "missing_profile"]:
        return (
            "missing_profile"
            if "error_status_code" in state
            else "profile_found"
        )

    def _assess_risk(
        self,
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        risk = cast(
            RiskAssessment,
            self.tool_registry.execute(ASSESS_RISK_TOOL, state["profile"]),
        )
        return {"risk": risk}

    @staticmethod
    def _route_after_risk(
        state: TrainingPlanAgentState,
    ) -> Literal["safe_to_plan", "blocked"]:
        return "safe_to_plan" if state["risk"].can_auto_plan else "blocked"

    @staticmethod
    def _block_automatic_planning(
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        return {
            "error_status_code": HTTPStatus.CONFLICT,
            "error_detail": {
                "message": "Automatic plan generation is blocked.",
                "risk": state["risk"].model_dump(),
            },
        }

    def _generate_plan(
        self,
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        plan = cast(
            TrainingPlanDraft,
            self.tool_registry.execute(
                GENERATE_TRAINING_PLAN_TOOL,
                state["profile"],
            ),
        )
        return {"plan": plan}

    def _validate_plan(
        self,
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        safety_check = cast(
            SafetyCheckResult,
            self.tool_registry.execute(
                VALIDATE_TRAINING_PLAN_TOOL,
                state["plan"],
            ),
        )
        return {"safety_check": safety_check}

    @staticmethod
    def _route_after_safety_check(
        state: TrainingPlanAgentState,
    ) -> Literal["safe_plan", "unsafe_plan"]:
        return "safe_plan" if state["safety_check"].valid else "unsafe_plan"

    @staticmethod
    def _reject_unsafe_plan(
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        return {
            "error_status_code": HTTPStatus.UNPROCESSABLE_ENTITY,
            "error_detail": {
                "message": "Generated plan failed safety check.",
                "safety_check": state["safety_check"].model_dump(),
            },
        }

    def _save_plan(
        self,
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        saved_plan = cast(
            TrainingPlanHistoryItem,
            self.tool_registry.execute(
                SAVE_TRAINING_PLAN_TOOL,
                SaveTrainingPlanInput(
                    user_id=state["user_id"],
                    plan=state["plan"],
                    safety_check=state["safety_check"],
                ),
            ),
        )
        return {"saved_plan": saved_plan}


def create_training_plan_agent(
    *,
    profile_repository: ProfileRepositoryPort,
    training_plan_repository: TrainingPlanRepositoryPort,
    tool_registry: ToolRegistry | None = None,
) -> TrainingPlanAgent:
    return TrainingPlanAgent(
        tool_registry=tool_registry
        or create_training_plan_tool_registry(
            profile_repository=profile_repository,
            training_plan_repository=training_plan_repository,
        )
    )
