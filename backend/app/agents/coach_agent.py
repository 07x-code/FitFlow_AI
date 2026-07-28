from dataclasses import dataclass
from typing import cast

from app.agents.core import Agent, AgentConfig
from app.agents.tools.fitness import (
    ASSESS_RISK_TOOL,
    GET_LATEST_TRAINING_PLAN_TOOL,
    GET_PROFILE_TOOL,
    RECALL_USER_MEMORY_TOOL,
    RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
    KnowledgeQuery,
    create_coach_tool_registry,
)
from app.agents.tools.registry import ToolRegistry
from app.domain.models import (
    CoachChatRequest,
    CoachChatResponse,
    FitnessKnowledgeItem,
    FitnessProfileCreate,
    KnowledgeSource,
    RiskAssessment,
    TrainingPlanHistoryItem,
    UserMemoryResponse,
)
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.infrastructure.user_memory_repository import UserMemoryRepository
from app.services.knowledge_retriever import KnowledgeRetriever
from app.services.llm_provider import LLMProvider, create_llm_provider


COACH_SYSTEM_PROMPT = (
    "你是 FitFlow AI 的健身教练。只能基于已经通过后端安全规则的"
    "用户画像、训练计划、记忆与本地知识回答。"
)


@dataclass(frozen=True)
class CoachAgentInput:
    user_id: str
    request: CoachChatRequest


class CoachAgent(Agent[CoachAgentInput, CoachChatResponse | None]):
    """Tool-using conversational agent with deterministic risk gating."""

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        llm_provider: LLMProvider,
        config: AgentConfig | None = None,
    ) -> None:
        super().__init__(
            name="fitflow-coach-agent",
            system_prompt=COACH_SYSTEM_PROMPT,
            config=config,
        )
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider

    def run(
        self,
        agent_input: CoachAgentInput,
        **kwargs: object,
    ) -> CoachChatResponse | None:
        profile = cast(
            FitnessProfileCreate | None,
            self.tool_registry.execute(
                GET_PROFILE_TOOL,
                agent_input.user_id,
            ),
        )
        if profile is None:
            return None

        risk = cast(
            RiskAssessment,
            self.tool_registry.execute(ASSESS_RISK_TOOL, profile),
        )
        if not risk.can_auto_plan:
            response = CoachChatResponse(
                answer=(
                    f"你的健康风险等级为 {risk.level}，系统不会提供自动训练建议。"
                    "如果出现胸痛、急性损伤或明显不适，请停止训练并咨询专业人士。"
                ),
                safety_level=risk.level,
                referenced_plan_id=None,
            )
            self.record_exchange(agent_input.request.message, response.answer)
            return response

        latest_plan = cast(
            TrainingPlanHistoryItem | None,
            self.tool_registry.execute(
                GET_LATEST_TRAINING_PLAN_TOOL,
                agent_input.user_id,
            ),
        )
        memories = cast(
            list[UserMemoryResponse],
            self.tool_registry.execute(
                RECALL_USER_MEMORY_TOOL,
                agent_input.user_id,
            ),
        )
        knowledge_items = cast(
            list[FitnessKnowledgeItem],
            self.tool_registry.execute(
                RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
                KnowledgeQuery(query=agent_input.request.message),
            ),
        )
        completion = self.llm_provider.complete(
            build_coach_chat_prompt(
                profile=profile,
                latest_plan=latest_plan,
                memories=memories,
                knowledge_items=knowledge_items,
                risk_level=risk.level,
                message=agent_input.request.message,
            )
        )

        response = CoachChatResponse(
            answer=completion.content.strip(),
            safety_level=risk.level,
            referenced_plan_id=latest_plan.id if latest_plan is not None else None,
            knowledge_sources=[
                KnowledgeSource(
                    title=item.title,
                    category=item.category,
                    summary=item.summary,
                )
                for item in knowledge_items
            ],
        )
        self.record_exchange(agent_input.request.message, response.answer)
        return response

    def chat(
        self,
        user_id: str,
        request: CoachChatRequest,
    ) -> CoachChatResponse | None:
        """Compatibility-friendly API for the existing FastAPI endpoint."""

        return self.run(CoachAgentInput(user_id=user_id, request=request))


def create_coach_agent(
    *,
    profile_repository: ProfileRepository,
    training_plan_repository: TrainingPlanRepository,
    llm_provider: LLMProvider | None = None,
    memory_repository: UserMemoryRepository | None = None,
    knowledge_retriever: KnowledgeRetriever | None = None,
    tool_registry: ToolRegistry | None = None,
    config: AgentConfig | None = None,
) -> CoachAgent:
    memory_repository = memory_repository or UserMemoryRepository()
    knowledge_retriever = (
        knowledge_retriever or KnowledgeRetriever.from_default_file()
    )
    return CoachAgent(
        tool_registry=tool_registry
        or create_coach_tool_registry(
            profile_repository=profile_repository,
            training_plan_repository=training_plan_repository,
            memory_repository=memory_repository,
            knowledge_retriever=knowledge_retriever,
        ),
        llm_provider=llm_provider or create_llm_provider(),
        config=config,
    )


def build_coach_chat_prompt(
    *,
    profile: FitnessProfileCreate,
    latest_plan: TrainingPlanHistoryItem | None,
    memories: list[UserMemoryResponse],
    knowledge_items: list[FitnessKnowledgeItem],
    risk_level: str,
    message: str,
) -> str:
    latest_plan_context = "用户还没有历史训练计划。"
    if latest_plan is not None:
        latest_plan_context = (
            f"最近训练计划 ID：{latest_plan.id}，"
            f"每周训练天数：{len(latest_plan.plan.days)}，"
            f"安全校验通过：{latest_plan.safety_check.valid}。"
        )

    memory_context = "用户还没有长期记忆。"
    if memories:
        memory_context = "\n".join(
            f"- {memory.type}: {memory.content}" for memory in memories
        )

    knowledge_context = "未检索到与当前问题直接相关的本地健身知识。"
    if knowledge_items:
        knowledge_context = "\n".join(
            (
                f"- 标题：{item.title}\n"
                f"  分类：{item.category}\n"
                f"  内容：{item.content}"
            )
            for item in knowledge_items
        )

    prompt = (
        f"{COACH_SYSTEM_PROMPT}\n"
        "要求：不要诊断疾病，不要提供康复处方，不要绕过安全规则；"
        "如果问题涉及疼痛、胸痛、急性损伤或明显不适，要提醒停止训练并咨询专业人士。\n\n"
        f"用户问题：{message}\n"
        f"用户画像：年龄 {profile.age}，目标 {profile.goal}，"
        f"每周计划训练 {profile.sessions_per_week} 天，每次 {profile.session_minutes} 分钟。\n"
        f"风险等级：{risk_level}\n"
        f"长期记忆：\n{memory_context}\n"
        f"训练计划上下文：{latest_plan_context}"
    )
    return f"{prompt}\n健身知识库依据：\n{knowledge_context}"
