from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from app.ai.core import Agent
from app.ai.orchestration import (
    TrainingPlanAgentState,
    create_training_plan_graph,
)
from app.ai.tools.fitness import create_training_plan_tool_registry
from app.ai.tools.registry import ToolRegistry
from app.domain.models import TrainingPlanDraftResponse
from app.ports.repositories import (
    ProfileRepositoryPort,
)


@dataclass(frozen=True)
class TrainingPlanAgentResult:
    """训练计划 Agent 的运行结果。"""

    status_code: int
    response: TrainingPlanDraftResponse | None = None
    error_detail: Any = None


class TrainingPlanAgent(Agent[str, TrainingPlanAgentResult]):
    """带有确定性安全门禁的规划与求解 Agent。"""

    def __init__(self, *, tool_registry: ToolRegistry) -> None:
        """
        初始化训练计划 Agent。

        :param tool_registry: 训练计划流程允许调用的工具注册表。
        :return: 无返回值。
        """
        super().__init__(
            name="training-plan-agent",
            system_prompt=(
                "Create beginner plans only after profile and risk checks, "
                "and return only plans that pass deterministic validation."
            ),
        )
        self.tool_registry = tool_registry
        self.graph = create_training_plan_graph(tool_registry)

    def run(
        self,
        agent_input: str,
        **kwargs: object,
    ) -> TrainingPlanAgentResult:
        """
        为指定用户执行训练计划工作流。

        :param agent_input: 用户标识。
        :param kwargs: 预留的 Agent 扩展参数。
        :return: 训练计划生成结果。
        """
        final_state: TrainingPlanAgentState = self.graph.invoke(
            {"user_id": agent_input}
        )
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


def create_training_plan_agent(
    *,
    profile_repository: ProfileRepositoryPort,
    tool_registry: ToolRegistry | None = None,
) -> TrainingPlanAgent:
    """
    创建完成工具装配的训练计划 Agent。

    :param profile_repository: 用户画像仓储端口。
    :param tool_registry: 可选的自定义工具注册表。
    :return: 已完成依赖装配的训练计划 Agent。
    """
    return TrainingPlanAgent(
        tool_registry=tool_registry
        or create_training_plan_tool_registry(
            profile_repository=profile_repository,
        )
    )
