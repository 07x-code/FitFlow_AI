from datetime import date
from dataclasses import dataclass

from app.ai.tools.base import Tool, ToolParameter
from app.ai.tools.registry import ToolRegistry
from app.domain.models import (
    FitnessKnowledgeItem,
    FitnessProfileCreate,
    RiskAssessment,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanHistoryItem,
    UserMemoryResponse,
)
from app.domain.plan_generator import generate_beginner_plan
from app.domain.plan_schedule import get_next_week_start
from app.domain.risk_rules import assess_risk
from app.domain.training_rules import validate_beginner_plan
from app.ports.knowledge import KnowledgeRetrieverPort
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanRepositoryPort,
    UserMemoryRepositoryPort,
)


GET_PROFILE_TOOL = "get_profile"
ASSESS_RISK_TOOL = "assess_risk"
GENERATE_TRAINING_PLAN_TOOL = "generate_training_plan"
VALIDATE_TRAINING_PLAN_TOOL = "validate_training_plan"

GET_LATEST_TRAINING_PLAN_TOOL = "get_latest_training_plan"
RECALL_USER_MEMORY_TOOL = "recall_user_memory"
RETRIEVE_FITNESS_KNOWLEDGE_TOOL = "retrieve_fitness_knowledge"





@dataclass(frozen=True)
class KnowledgeQuery:
    query: str
    limit: int = 3


class GetProfileTool(Tool[str, FitnessProfileCreate | None]):
    def __init__(self, repository: ProfileRepositoryPort) -> None:
        super().__init__(
            name=GET_PROFILE_TOOL,
            description="加载用户已校验的健身画像。",
            parameters=(
                ToolParameter(
                    name="user_id",
                    description="稳定的 FitFlow 用户标识。",
                ),
            ),
        )
        self.repository = repository

    def run(self, tool_input: str) -> FitnessProfileCreate | None:
        return self.repository.get(tool_input)


class AssessRiskTool(Tool[FitnessProfileCreate, RiskAssessment]):
    def __init__(self) -> None:
        super().__init__(
            name=ASSESS_RISK_TOOL,
            description="对用户画像应用确定性的健康风险规则。",
            parameters=(
                ToolParameter(
                    name="profile",
                    description="已校验的健身画像。",
                    type_name="FitnessProfileCreate",
                ),
            ),
        )

    def run(self, tool_input: FitnessProfileCreate) -> RiskAssessment:
        return RiskAssessment.model_validate(assess_risk(tool_input))


class GenerateTrainingPlanTool(
    Tool[FitnessProfileCreate, TrainingPlanDraft]
):
    def __init__(self) -> None:
        super().__init__(
            name=GENERATE_TRAINING_PLAN_TOOL,
            description="生成确定性的初学者训练计划。",
            parameters=(
                ToolParameter(
                    name="profile",
                    description="已校验的低风险健身画像。",
                    type_name="FitnessProfileCreate",
                ),
            ),
        )

    def run(self, tool_input: FitnessProfileCreate) -> TrainingPlanDraft:
        """
        根据用户画像生成默认目标为下周的训练计划。

        :param tool_input: 已通过风险检查的用户健身画像。
        :return: 包含目标周信息的训练计划草案。
        """
        return generate_beginner_plan(
            tool_input,
            week_start=get_next_week_start(date.today()),
            timezone="Asia/Shanghai",
            goal_summary=(
                f"围绕 {tool_input.goal.value} 目标安排下周训练。"
            ),
        )


class ValidateTrainingPlanTool(
    Tool[TrainingPlanDraft, SafetyCheckResult]
):
    def __init__(self) -> None:
        super().__init__(
            name=VALIDATE_TRAINING_PLAN_TOOL,
            description="按照初学者安全规则检查生成的训练计划。",
            parameters=(
                ToolParameter(
                    name="plan",
                    description="已生成的训练计划。",
                    type_name="TrainingPlanDraft",
                ),
            ),
        )

    def run(self, tool_input: TrainingPlanDraft) -> SafetyCheckResult:
        return SafetyCheckResult.model_validate(validate_beginner_plan(tool_input))





class GetLatestTrainingPlanTool(
    Tool[str, TrainingPlanHistoryItem | None]
):
    def __init__(self, repository: TrainingPlanRepositoryPort) -> None:
        super().__init__(
            name=GET_LATEST_TRAINING_PLAN_TOOL,
            description="加载用户最近生成的训练计划。",
            parameters=(
                ToolParameter(
                    name="user_id",
                    description="稳定的 FitFlow 用户标识。",
                ),
            ),
        )
        self.repository = repository

    def run(self, tool_input: str) -> TrainingPlanHistoryItem | None:
        plans = self.repository.list_by_user(tool_input)
        return plans[0] if plans else None


class RecallUserMemoryTool(Tool[str, list[UserMemoryResponse]]):
    def __init__(self, repository: UserMemoryRepositoryPort) -> None:
        super().__init__(
            name=RECALL_USER_MEMORY_TOOL,
            description="召回为用户保存的显式长期记忆。",
            parameters=(
                ToolParameter(
                    name="user_id",
                    description="稳定的 FitFlow 用户标识。",
                ),
            ),
        )
        self.repository = repository

    def run(self, tool_input: str) -> list[UserMemoryResponse]:
        return self.repository.list_by_user(tool_input)


class RetrieveFitnessKnowledgeTool(
    Tool[KnowledgeQuery, list[FitnessKnowledgeItem]]
):
    def __init__(self, retriever: KnowledgeRetrieverPort) -> None:
        super().__init__(
            name=RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
            description="从本地健身 RAG 知识库中检索相关条目。",
            parameters=(
                ToolParameter(
                    name="query",
                    description="用户的健身问题。",
                ),
                ToolParameter(
                    name="limit",
                    description="最多返回的知识条目数量。",
                    type_name="integer",
                    required=False,
                    default=3,
                ),
            ),
        )
        self.retriever = retriever

    def run(self, tool_input: KnowledgeQuery) -> list[FitnessKnowledgeItem]:
        return self.retriever.retrieve(
            tool_input.query,
            limit=tool_input.limit,
        )


def create_training_plan_tool_registry(
    *,
    profile_repository: ProfileRepositoryPort,
) -> ToolRegistry:
    """
    创建只负责生成和校验草案的训练计划工具注册表。

    :param profile_repository: 用户画像仓储端口。
    :return: 已注册确定性规划工具的注册表。
    """
    registry = ToolRegistry()
    registry.register(GetProfileTool(profile_repository))
    registry.register(AssessRiskTool())
    registry.register(GenerateTrainingPlanTool())
    registry.register(ValidateTrainingPlanTool())
    return registry


def create_coach_tool_registry(
    *,
    profile_repository: ProfileRepositoryPort,
    training_plan_repository: TrainingPlanRepositoryPort,
    memory_repository: UserMemoryRepositoryPort,
    knowledge_retriever: KnowledgeRetrieverPort,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GetProfileTool(profile_repository))
    registry.register(AssessRiskTool())
    registry.register(GetLatestTrainingPlanTool(training_plan_repository))
    registry.register(RecallUserMemoryTool(memory_repository))
    registry.register(RetrieveFitnessKnowledgeTool(knowledge_retriever))
    return registry
