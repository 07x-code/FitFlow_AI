from dataclasses import dataclass

from app.domain.models import (
    CoachChatRequest,
    CoachChatResponse,
    FitnessKnowledgeItem,
    FitnessProfileCreate,
    KnowledgeSource,
    TrainingPlanHistoryItem,
    UserMemoryResponse,
)
from app.domain.risk_rules import assess_risk
from app.infrastructure.profile_repository import ProfileRepository
from app.infrastructure.training_plan_repository import TrainingPlanRepository
from app.infrastructure.user_memory_repository import UserMemoryRepository
from app.services.knowledge_retriever import KnowledgeRetriever
from app.services.llm_provider import LLMProvider, create_llm_provider


@dataclass(frozen=True)
class CoachChatService:
    profile_repository: ProfileRepository
    training_plan_repository: TrainingPlanRepository
    memory_repository: UserMemoryRepository
    knowledge_retriever: KnowledgeRetriever
    llm_provider: LLMProvider

    def chat(self, user_id: str, request: CoachChatRequest) -> CoachChatResponse | None:
        profile = self.profile_repository.get(user_id)
        if profile is None:
            return None

        risk = assess_risk(profile)
        if risk["can_auto_plan"] is False:
            return CoachChatResponse(
                answer=(
                    f"你的健康风险等级为 {risk['level']}，系统不会提供自动训练建议。"
                    "如果出现胸痛、急性损伤或明显不适，请停止训练并咨询专业人士。"
                ),
                safety_level=str(risk["level"]),
                referenced_plan_id=None,
            )

        latest_plan = self._get_latest_plan(user_id)
        memories = self.memory_repository.list_by_user(user_id)
        knowledge_items = self.knowledge_retriever.retrieve(request.message)
        completion = self.llm_provider.complete(
            _build_coach_chat_prompt(
                profile=profile,
                latest_plan=latest_plan,
                memories=memories,
                knowledge_items=knowledge_items,
                risk_level=str(risk["level"]),
                message=request.message,
            )
        )

        return CoachChatResponse(
            answer=completion.content.strip(),
            safety_level=str(risk["level"]),
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

    def _get_latest_plan(self, user_id: str) -> TrainingPlanHistoryItem | None:
        plans = self.training_plan_repository.list_by_user(user_id)
        if not plans:
            return None

        return plans[0]


def create_coach_chat_service(
    profile_repository: ProfileRepository,
    training_plan_repository: TrainingPlanRepository,
    llm_provider: LLMProvider | None = None,
    memory_repository: UserMemoryRepository | None = None,
    knowledge_retriever: KnowledgeRetriever | None = None,
) -> CoachChatService:
    return CoachChatService(
        profile_repository=profile_repository,
        training_plan_repository=training_plan_repository,
        memory_repository=memory_repository or UserMemoryRepository(),
        knowledge_retriever=(
            knowledge_retriever or KnowledgeRetriever.from_default_file()
        ),
        llm_provider=llm_provider or create_llm_provider(),
    )


def _build_coach_chat_prompt(
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
            f"最近训练计划 ID：{latest_plan.id}；"
            f"每周训练天数：{len(latest_plan.plan.days)}；"
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
        "你是 FitFlow AI 的健身教练，请基于后端已经通过安全规则的上下文回答用户。\n"
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
