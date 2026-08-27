from http import HTTPStatus
from typing import Any, Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from app.ai.tools.fitness import (
    ASSESS_RISK_TOOL,
    GENERATE_TRAINING_PLAN_TOOL,
    GET_PROFILE_TOOL,
    
    VALIDATE_TRAINING_PLAN_TOOL,
    
)
from app.ai.tools.registry import ToolRegistry
from app.domain.models import (
    FitnessProfileCreate,
    RiskAssessment,
    SafetyCheckResult,
    TrainingPlanDraft,
)


class TrainingPlanAgentState(TypedDict, total=False):
    """训练计划 LangGraph 的共享状态。"""

    user_id: str
    profile: FitnessProfileCreate
    risk: RiskAssessment
    plan: TrainingPlanDraft
    safety_check: SafetyCheckResult
    error_status_code: int
    error_detail: Any


class TrainingPlanGraphBuilder:
    """使用类型化工具构建训练计划 LangGraph。"""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        """
        初始化训练计划图构建器。

        :param tool_registry: 训练计划流程允许调用的工具注册表。
        :return: 无返回值。
        """
        self.tool_registry = tool_registry

    def build(self):
        """
        构建并编译训练计划工作流。

        :return: 可执行的 LangGraph 训练计划图。
        """
        workflow = StateGraph(TrainingPlanAgentState)
        workflow.add_node("load_profile", self._load_profile)
        workflow.add_node("assess_risk", self._assess_risk)
        workflow.add_node(
            "block_automatic_planning",
            self._block_automatic_planning,
        )
        workflow.add_node("generate_plan", self._generate_plan)
        workflow.add_node("validate_plan", self._validate_plan)
        workflow.add_node("reject_unsafe_plan", self._reject_unsafe_plan)
        

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
                "safe_plan": END,
                "unsafe_plan": "reject_unsafe_plan",
            },
        )
        workflow.add_edge("reject_unsafe_plan", END)
        return workflow.compile()

    def _load_profile(
        self,
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        """
        从工具端口加载用户画像。

        :param state: 当前工作流状态。
        :return: 包含画像或未找到错误的状态更新。
        """
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
        """
        根据画像加载结果选择后续节点。

        :param state: 当前工作流状态。
        :return: 画像存在或缺失的路由名称。
        """
        return (
            "missing_profile"
            if "error_status_code" in state
            else "profile_found"
        )

    def _assess_risk(
        self,
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        """
        使用确定性工具评估画像风险。

        :param state: 包含用户画像的工作流状态。
        :return: 包含风险评估的状态更新。
        """
        risk = cast(
            RiskAssessment,
            self.tool_registry.execute(ASSESS_RISK_TOOL, state["profile"]),
        )
        return {"risk": risk}

    @staticmethod
    def _route_after_risk(
        state: TrainingPlanAgentState,
    ) -> Literal["safe_to_plan", "blocked"]:
        """
        根据风险结果决定是否允许生成计划。

        :param state: 包含风险评估的工作流状态。
        :return: 允许规划或阻止规划的路由名称。
        """
        return "safe_to_plan" if state["risk"].can_auto_plan else "blocked"

    @staticmethod
    def _block_automatic_planning(
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        """
        为高风险用户生成阻止自动规划的错误状态。

        :param state: 包含风险评估的工作流状态。
        :return: 包含冲突错误的状态更新。
        """
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
        """
        使用计划工具生成初学者训练计划。

        :param state: 包含低风险用户画像的工作流状态。
        :return: 包含训练计划的状态更新。
        """
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
        """
        使用确定性规则校验生成的训练计划。

        :param state: 包含训练计划的工作流状态。
        :return: 包含安全检查的状态更新。
        """
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
        """
        根据安全校验结果决定保存或拒绝计划。

        :param state: 包含安全检查的工作流状态。
        :return: 安全计划或拒绝计划的路由名称。
        """
        return "safe_plan" if state["safety_check"].valid else "unsafe_plan"

    @staticmethod
    def _reject_unsafe_plan(
        state: TrainingPlanAgentState,
    ) -> TrainingPlanAgentState:
        """
        为未通过安全检查的计划生成错误状态。

        :param state: 包含失败安全检查的工作流状态。
        :return: 包含不可处理错误的状态更新。
        """
        return {
            "error_status_code": HTTPStatus.UNPROCESSABLE_ENTITY,
            "error_detail": {
                "message": "Generated plan failed safety check.",
                "safety_check": state["safety_check"].model_dump(),
            },
        }



def create_training_plan_graph(tool_registry: ToolRegistry):
    """
    创建可由 TrainingPlanAgent 调用的 LangGraph。

    :param tool_registry: 训练计划流程允许调用的工具注册表。
    :return: 已编译的训练计划工作流。
    """
    return TrainingPlanGraphBuilder(tool_registry).build()
