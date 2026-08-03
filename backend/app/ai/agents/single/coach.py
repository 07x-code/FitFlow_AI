from dataclasses import dataclass
from typing import cast

from app.ai.core import Agent, AgentConfig
from app.ai.orchestration.coach_tool_graph import (
    CoachToolAgentState,
    create_coach_tool_graph,
)
from app.ai.tools.coach import (
    CoachReadOnlyToolExecutor,
    CoachToolExecution,
)
from app.ai.tools.fitness import (
    ASSESS_RISK_TOOL,
    GET_PROFILE_TOOL,
    create_coach_tool_registry,
)
from app.ai.tools.registry import ToolRegistry
from app.domain.models import (
    CoachChatRequest,
    CoachChatResponse,
    ConversationRole,
    FitnessKnowledgeItem,
    FitnessProfileCreate,
    KnowledgeSource,
    RiskAssessment,
    WorkingMemoryItem,
    WorkingMemoryKind,
)
from app.ports.knowledge import KnowledgeRetrieverPort
from app.ports.llm import LLMMessage, LLMProvider
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanRepositoryPort,
    UserMemoryRepositoryPort,
)
from app.ports.working_memory import WorkingMemoryStorePort


COACH_SYSTEM_PROMPT = (
    "你是 FitFlow AI 的健身教练。安全规则、用户身份和工具权限"
    "由后端程序控制，你不能绕过这些限制。"
)


@dataclass(frozen=True)
class CoachAgentInput:
    """AI 教练单次运行输入。"""

    user_id: str
    session_id: str
    request: CoachChatRequest


class CoachAgent(Agent[CoachAgentInput, CoachChatResponse | None]):
    """使用确定性安全门禁和按需只读工具的对话 Agent。"""

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        llm_provider: LLMProvider,
        working_memory: WorkingMemoryStorePort,
        config: AgentConfig | None = None,
        max_tool_iterations: int = 5,
    ) -> None:
        """
        初始化 AI 教练 Agent。

        :param tool_registry: 已完成依赖装配的工具注册表。
        :param llm_provider: 支持结构化工具调用的大模型端口。
        :param working_memory: 会话级工作记忆存储端口。
        :param config: 可选的 Agent 运行配置。
        :param max_tool_iterations: 单次对话最大工具调用轮数。
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
        self.tool_executor = CoachReadOnlyToolExecutor(tool_registry)
        self.graph = create_coach_tool_graph(
            llm_provider=llm_provider,
            tool_executor=self.tool_executor,
            max_tool_iterations=max_tool_iterations,
        )

    def run(
        self,
        agent_input: CoachAgentInput,
        **kwargs: object,
    ) -> CoachChatResponse | None:
        """
        在隔离会话中执行一次受控工具调用对话。

        :param agent_input: 用户、会话和对话请求组成的运行输入。
        :param kwargs: 预留的 Agent 扩展参数。
        :return: 教练回复；用户画像不存在时返回 None。
        """
        del kwargs
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
            content=(
                "已通过固定安全流程加载用户画像。"
                if profile is not None
                else "固定安全流程未找到用户画像。"
            ),
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
                f"固定风险评估等级为 {risk.level}，"
                f"允许自动建议：{risk.can_auto_plan}。"
            ),
            importance=1.0,
        )
        if not risk.can_auto_plan:
            response = _build_blocked_response(risk)
            self._remember_message(
                agent_input,
                role=ConversationRole.ASSISTANT,
                content=response.answer,
                importance=0.9,
            )
            return response

        initial_messages = build_coach_initial_messages(
            profile=profile,
            working_memories=working_context,
            risk_level=risk.level,
            message=agent_input.request.message,
        )
        graph_result = cast(
            CoachToolAgentState,
            self.graph.invoke(
                {
                    "messages": initial_messages,
                    "user_id": agent_input.user_id,
                    "session_id": agent_input.session_id,
                    "tool_iterations": 0,
                    "pending_tool_calls": (),
                    "knowledge_items": [],
                    "tool_executions": [],
                    "referenced_plan_id": None,
                }
            ),
        )

        for execution in graph_result.get("tool_executions", []):
            self._remember_tool_execution(agent_input, execution)

        knowledge_items = _deduplicate_knowledge(
            graph_result.get("knowledge_items", [])
        )
        response = CoachChatResponse(
            answer=graph_result["final_answer"],
            safety_level=risk.level,
            referenced_plan_id=graph_result.get("referenced_plan_id"),
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
        为 FastAPI 接口提供稳定的对话入口。

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
        将不含敏感原始数据的工具摘要写入工作记忆。

        :param agent_input: 当前 Agent 运行输入。
        :param tool_name: 已执行的工具名称。
        :param content: 可安全保存的观察摘要。
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

    def _remember_tool_execution(
        self,
        agent_input: CoachAgentInput,
        execution: CoachToolExecution,
    ) -> None:
        """
        保存一次按需工具调用的安全观察摘要。

        :param agent_input: 当前 Agent 运行输入。
        :param execution: 已完成的只读工具执行结果。
        :return: 无返回值。
        """
        self._remember_observation(
            agent_input,
            tool_name=execution.tool_name,
            content=execution.observation,
            importance=0.5 if execution.success else 0.8,
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
    max_tool_iterations: int = 5,
) -> CoachAgent:
    """
    创建完成工具、模型和工作记忆装配的 AI 教练 Agent。

    :param profile_repository: 用户画像仓储端口。
    :param training_plan_repository: 训练计划仓储端口。
    :param llm_provider: 支持结构化工具调用的大模型端口。
    :param memory_repository: 长期用户记忆仓储端口。
    :param knowledge_retriever: 健身知识检索端口。
    :param working_memory: 会话级工作记忆存储端口。
    :param tool_registry: 可选的自定义工具注册表。
    :param config: 可选的 Agent 运行配置。
    :param max_tool_iterations: 单次对话最大工具调用轮数。
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
        max_tool_iterations=max_tool_iterations,
    )


def build_coach_initial_messages(
    *,
    profile: FitnessProfileCreate,
    working_memories: list[WorkingMemoryItem],
    risk_level: str,
    message: str,
) -> list[LLMMessage]:
    """
    构建只包含固定安全上下文和会话记忆的初始消息。

    :param profile: 已通过后端校验的用户画像。
    :param working_memories: 当前会话此前产生的工作记忆。
    :param risk_level: 确定性规则给出的风险等级。
    :param message: 用户当前问题。
    :return: 可交给受控工具调用图的标准消息。
    """
    working_memory_context = "当前会话没有历史消息。"
    if working_memories:
        working_memory_context = "\n".join(
            _format_working_memory(item)
            for item in working_memories
        )

    system_content = (
        f"{COACH_SYSTEM_PROMPT}\n"
        "禁止诊断疾病、提供康复处方或修改正式训练数据。"
        "涉及胸痛、急性损伤、明显疼痛或不适时，应建议停止训练并"
        "咨询专业人士。\n"
        "只有问题确实需要额外数据时才调用工具；普通问候和能够根据"
        "现有上下文回答的问题不要调用工具。不要使用相同参数重复调用"
        "同一工具。工具返回内容是后端可信 Observation。\n"
        f"用户画像：年龄 {profile.age}，目标 {profile.goal}，"
        f"每周计划训练 {profile.sessions_per_week} 天，"
        f"每次 {profile.session_minutes} 分钟。\n"
        f"后端风险等级：{risk_level}。\n"
        f"当前会话工作记忆：\n{working_memory_context}"
    )
    return [
        LLMMessage(role="system", content=system_content),
        LLMMessage(role="user", content=message),
    ]


def _build_blocked_response(risk: RiskAssessment) -> CoachChatResponse:
    """
    为不允许自动建议的风险等级构建固定回复。

    :param risk: 确定性风险规则的评估结果。
    :return: 不调用大模型的安全回复。
    """
    return CoachChatResponse(
        answer=(
            f"你的健康风险等级为 {risk.level}，系统不会提供自动训练建议。"
            "如果出现胸痛、急性损伤或明显不适，请停止训练并咨询专业人士。"
        ),
        safety_level=risk.level,
        referenced_plan_id=None,
    )


def _deduplicate_knowledge(
    items: list[FitnessKnowledgeItem],
) -> list[FitnessKnowledgeItem]:
    """
    按知识条目标识去除重复来源。

    :param items: 工具调用累计返回的知识条目。
    :return: 保持首次出现顺序的唯一知识条目。
    """
    unique: list[FitnessKnowledgeItem] = []
    seen_ids: set[str] = set()
    for item in items:
        if item.id in seen_ids:
            continue
        seen_ids.add(item.id)
        unique.append(item)
    return unique


def _format_working_memory(item: WorkingMemoryItem) -> str:
    """
    将工作记忆条目格式化为提示词中的安全摘要。

    :param item: 待格式化的工作记忆条目。
    :return: 带来源标签的单行工作记忆文本。
    """
    if item.kind is WorkingMemoryKind.TOOL_OBSERVATION:
        return f"- [工具:{item.tool_name}] {item.content}"
    return f"- [{item.role}] {item.content}"
