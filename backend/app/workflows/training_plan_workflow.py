"""为原工作流接口保留向后兼容导入。

LangGraph 编排逻辑现已放入 :class:`TrainingPlanAgent`，本
模块继续保证 API 客户端和测试中的旧导入可用。
"""

from app.agents.tools.registry import ToolRegistry
from app.agents.training_plan_agent import (
    TrainingPlanAgent,
    TrainingPlanAgentResult,
    TrainingPlanAgentState,
    create_training_plan_agent,
)
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository


TrainingPlanWorkflow = TrainingPlanAgent
TrainingPlanWorkflowResult = TrainingPlanAgentResult
TrainingPlanWorkflowState = TrainingPlanAgentState


def create_training_plan_workflow(
    profile_repository: ProfileRepository,
    training_plan_repository: TrainingPlanRepository,
    tool_registry: ToolRegistry | None = None,
) -> TrainingPlanWorkflow:
    return create_training_plan_agent(
        profile_repository=profile_repository,
        training_plan_repository=training_plan_repository,
        tool_registry=tool_registry,
    )
