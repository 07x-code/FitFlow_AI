from dataclasses import dataclass
from typing import cast

from app.ai.core import Agent, AgentConfig
from app.ai.tools.fitness import (
    ASSESS_RISK_TOOL,
    GET_LATEST_TRAINING_PLAN_TOOL,
    GET_PROFILE_TOOL,
    RECALL_USER_MEMORY_TOOL,
    RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
    KnowledgeQuery,
    create_coach_tool_registry,
)
from app.ai.tools.registry import ToolRegistry
from app.domain.memory import (
    ConversationRole,
    WorkingMemoryItem,
    WorkingMemoryKind,
)
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
from app.ports.knowledge import KnowledgeRetrieverPort
from app.ports.llm import LLMProvider
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanRepositoryPort,
    UserMemoryRepositoryPort,
)
from app.ports.working_memory import WorkingMemoryStorePort


COACH_SYSTEM_PROMPT = (
    "你是 FitFlow AI 的健身教练。只能基于已经通过后端安全规则的"
    "用户画像、训练计划、记忆与本地知识回答。"
)


@dataclass(frozen=True)
class CoachAgentInput:
    """AI 教练单次运行输入。"""

    user_id: str
    session_id: str
    request: CoachChatRequest


class CoachAgent(Agent[CoachAgentInput, CoachChatResponse | None]):
    """使用工具、工作记忆和确定性风险门禁的对话 Agent。"""

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        llm_provider: LLMProvider,
        working_memory: WorkingMemoryStorePort,
        config: AgentConfig | None = None,
    ) -> None:
        """
        初始化 AI 教练 Agent。

        :param tool_registry: 教练可调用的工具注册表。
        :param llm_provider: 大模型调用端口。
        :param working_memory: 会话级工作记忆存储端口。
        :param config: 可选的 Agent 运行配置。
        :return: 无返回值。
        """
        super().__init__(
            name="fitflow-coach-agent",
            system_prompt=COACH_SYSTEM_PROMPT,
            config=config,
        )
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider
        self.working_memory = working_memory

    def run(
        self,
        agent_input: CoachAgentInput,
        **kwargs: object,
    ) -> CoachChatResponse | None:
        """
        在隔离会话中执行一次带工作记忆的教练对话。

        :param agent_input: 用户、会话和对话请求组成的运行输入。
        :param kwargs: 预留的 Agent 扩展参数。
        :return: 教练回复；用户画像不存在时返回 None。
        """
        working_context = self.working_memory.list(
            agent_input.user_id,
            agent_input.session_id,
            limit=20,
        )
        self._remember_message(
            agent_input,
            role=ConversationRole.USER,
            content=agent_input.request.message,
            importance=0.7,
        )

        profile = cast(
            FitnessProfileCreate | None,
            self.tool_registry.execute(
                GET_PROFILE_TOOL,
                agent_input.user_id,
            ),
        )
        self._remember_observation(
            agent_input,
            tool_name=GET_PROFILE_TOOL,
            content="已加载用户画像。" if profile is not None else "未找到用户画像。",
            importance=0.8,
        )
        if profile is None:
            return None

        risk = cast(
            RiskAssessment,
            self.tool_registry.execute(ASSESS_RISK_TOOL, profile),
        )
        self._remember_observation(
            agent_input,
            tool_name=ASSESS_RISK_TOOL,
            content=(
                f"风险等级为 {risk.level}；"
                f"允许自动建议：{risk.can_auto_plan}。"
            ),
            importance=1.0,
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
            self._remember_message(
                agent_input,
                role=ConversationRole.ASSISTANT,
                content=response.answer,
                importance=0.9,
            )
            return response

        latest_plan = cast(
            TrainingPlanHistoryItem | None,
            self.tool_registry.execute(
                GET_LATEST_TRAINING_PLAN_TOOL,
                agent_input.user_id,
            ),
        )
        self._remember_observation(
            agent_input,
            tool_name=GET_LATEST_TRAINING_PLAN_TOOL,
            content=(
                f"已加载训练计划 #{latest_plan.id}。"
                if latest_plan is not None
                else "用户暂无训练计划。"
            ),
        )
        memories = cast(
            list[UserMemoryResponse],
            self.tool_registry.execute(
                RECALL_USER_MEMORY_TOOL,
                agent_input.user_id,
            ),
        )
        self._remember_observation(
            agent_input,
            tool_name=RECALL_USER_MEMORY_TOOL,
            content=f"已召回 {len(memories)} 条长期记忆。",
        )
        knowledge_items = cast(
            list[FitnessKnowledgeItem],
            self.tool_registry.execute(
                RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
                KnowledgeQuery(query=agent_input.request.message),
            ),
        )
        self._remember_observation(
            agent_input,
            tool_name=RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
            content=f"已检索 {len(knowledge_items)} 条本地健身知识。",
        )
        completion = self.llm_provider.complete(
            build_coach_chat_prompt(
                profile=profile,
                latest_plan=latest_plan,
                memories=memories,
                working_memories=working_context,
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
        self._remember_message(
            agent_input,
            role=ConversationRole.ASSISTANT,
            content=response.answer,
            importance=0.7,
        )
        return response

    def chat(
        self,
        user_id: str,
        session_id: str,
        request: CoachChatRequest,
    ) -> CoachChatResponse | None:
        """
        为现有 FastAPI 接口保留兼容的对话调用入口。

        :param user_id: 当前用户的稳定标识。
        :param session_id: 当前对话的会话标识。
        :param request: 用户提交的教练对话请求。
        :return: 教练回复；用户画像不存在时返回 None。
        """
        return self.run(
            CoachAgentInput(
                user_id=user_id,
                session_id=session_id,
                request=request,
            )
        )

    def _remember_message(
        self,
        agent_input: CoachAgentInput,
        *,
        role: ConversationRole,
        content: str,
        importance: float,
    ) -> None:
        """
        将一条对话消息写入当前会话工作记忆。

        :param agent_input: 当前 Agent 运行输入。
        :param role: 消息角色。
        :param content: 消息内容。
        :param importance: 条目重要性。
        :return: 无返回值。
        """
        self.working_memory.append(
            agent_input.user_id,
            agent_input.session_id,
            WorkingMemoryItem(
                kind=WorkingMemoryKind.MESSAGE,
                role=role,
                content=content,
                importance=importance,
            ),
        )

    def _remember_observation(
        self,
        agent_input: CoachAgentInput,
        *,
        tool_name: str,
        content: str,
        importance: float = 0.5,
    ) -> None:
        """
        将工具执行摘要写入当前会话工作记忆。

        :param agent_input: 当前 Agent 运行输入。
        :param tool_name: 已执行的工具名称。
        :param content: 不含敏感原始数据的观察摘要。
        :param importance: 条目重要性。
        :return: 无返回值。
        """
        self.working_memory.append(
            agent_input.user_id,
            agent_input.session_id,
            WorkingMemoryItem(
                kind=WorkingMemoryKind.TOOL_OBSERVATION,
                tool_name=tool_name,
                content=content,
                importance=importance,
            ),
        )


def create_coach_agent(
    *,
    profile_repository: ProfileRepositoryPort,
    training_plan_repository: TrainingPlanRepositoryPort,
    llm_provider: LLMProvider,
    memory_repository: UserMemoryRepositoryPort,
    knowledge_retriever: KnowledgeRetrieverPort,
    working_memory: WorkingMemoryStorePort,
    tool_registry: ToolRegistry | None = None,
    config: AgentConfig | None = None,
) -> CoachAgent:
    """
    创建完成工具和工作记忆装配的 AI 教练 Agent。

    :param profile_repository: 用户画像仓储端口。
    :param training_plan_repository: 训练计划仓储端口。
    :param llm_provider: 大模型调用端口。
    :param memory_repository: 长期用户记忆仓储端口。
    :param knowledge_retriever: 健身知识检索端口。
    :param working_memory: 会话级工作记忆存储端口。
    :param tool_registry: 可选的自定义工具注册表。
    :param config: 可选的 Agent 运行配置。
    :return: 已完成依赖装配的 AI 教练 Agent。
    """
    return CoachAgent(
        tool_registry=tool_registry
        or create_coach_tool_registry(
            profile_repository=profile_repository,
            training_plan_repository=training_plan_repository,
            memory_repository=memory_repository,
            knowledge_retriever=knowledge_retriever,
        ),
        llm_provider=llm_provider,
        working_memory=working_memory,
        config=config,
    )


def build_coach_chat_prompt(
    *,
    profile: FitnessProfileCreate,
    latest_plan: TrainingPlanHistoryItem | None,
    memories: list[UserMemoryResponse],
    working_memories: list[WorkingMemoryItem],
    knowledge_items: list[FitnessKnowledgeItem],
    risk_level: str,
    message: str,
) -> str:
    """
    构建包含会话工作记忆的 AI 教练提示词。

    :param profile: 已通过校验的用户画像。
    :param latest_plan: 用户最近的训练计划。
    :param memories: 用户显式保存的长期记忆。
    :param working_memories: 当前会话此前产生的消息和工具观察。
    :param knowledge_items: 与当前问题相关的健身知识。
    :param risk_level: 确定性规则给出的风险等级。
    :param message: 用户当前问题。
    :return: 可交给大模型的完整提示词。
    """
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

    working_memory_context = "当前会话还没有历史工作记忆。"
    if working_memories:
        working_memory_context = "\n".join(
            _format_working_memory(item) for item in working_memories
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
        f"会话工作记忆：\n{working_memory_context}\n"
        f"长期记忆：\n{memory_context}\n"
        f"训练计划上下文：{latest_plan_context}"
    )
    return f"{prompt}\n健身知识库依据：\n{knowledge_context}"


def _format_working_memory(item: WorkingMemoryItem) -> str:
    """
    将工作记忆条目格式化为提示词中的安全摘要。

    :param item: 待格式化的工作记忆条目。
    :return: 带来源标签的单行工作记忆文本。
    """
    if item.kind is WorkingMemoryKind.TOOL_OBSERVATION:
        return f"- [工具:{item.tool_name}] {item.content}"
    return f"- [{item.role}] {item.content}"
