import asyncio

from app.application.use_cases.proposals import ProposalUseCases
from app.domain.models import (
    FitnessProfileCreate,
    MemoryType,
    ProposalOperation,
    ProposalStatus,
    ProposalType,
    TrainingPlanProposalResponse,
    UserMemoryResponse,
)
from app.ports.llm import LLMCompletion, LLMMessage, LLMToolCompletion


class ProfileRepositoryStub:
    """返回固定用户画像的测试仓储。"""

    async def get(self, user_id: str) -> FitnessProfileCreate:
        """
        返回可以自动生成计划的用户画像。

        :param user_id: 用户标识。
        :return: 固定的用户画像。
        """
        del user_id
        return FitnessProfileCreate(
            age=28,
            sex="male",
            height_cm=175,
            weight_kg=70,
            goal="muscle_gain",
            sessions_per_week=3,
            session_minutes=60,
            health_flags=[],
        )


class MemoryRepositoryStub:
    """记录长期记忆查询的测试仓储。"""

    def __init__(self) -> None:
        """
        初始化查询记录。

        :return: 无返回值。
        """
        self.requested_user_ids: list[str] = []

    async def list_by_user(self, user_id: str) -> list[UserMemoryResponse]:
        """
        返回用户明确保存的器械限制。

        :param user_id: 用户标识。
        :return: 用于计划生成的长期记忆。
        """
        self.requested_user_ids.append(user_id)
        return [
            UserMemoryResponse(
                id=1,
                type=MemoryType.PREFERRED_EQUIPMENT,
                content="训练时只使用哑铃，不使用固定器械。",
                source="user",
                created_at="2026-08-31T10:00:00+08:00",
            )
        ]


class ProposalRepositoryStub:
    """返回待确认提案的测试仓储。"""

    async def create(
        self,
        user_id: str,
        plan: object,
        safety_check: object,
    ) -> TrainingPlanProposalResponse:
        """
        将应用层生成的计划包装为提案响应。

        :param user_id: 用户标识。
        :param plan: 已参考长期记忆的训练计划。
        :param safety_check: 确定性安全检查结果。
        :return: 待用户确认的提案。
        """
        del user_id
        return TrainingPlanProposalResponse(
            id=1,
            type=ProposalType.TRAINING_PLAN,
            operation=ProposalOperation.CREATE,
            target_week_start=plan.week_start,
            revision=1,
            status=ProposalStatus.PENDING,
            plan=plan,
            safety_check=safety_check,
            generation_summary=plan.goal_summary,
            created_at="2026-08-31T10:00:00+08:00",
        )


class RecordingLLMProvider:
    """记录计划上下文并回传基础计划的测试模型。"""

    name = "recording"
    model = "recording-plan-model"

    def __init__(self) -> None:
        """
        初始化模型消息记录。

        :return: 无返回值。
        """
        self.messages: list[LLMMessage] = []

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: tuple[object, ...],
    ) -> LLMToolCompletion:
        """
        保存后端组装的消息并返回其中的基础计划。

        :param messages: 包含用户画像和长期记忆的模型消息。
        :param tools: 计划生成不允许使用的工具定义。
        :return: 结构保持不变的计划补全结果。
        """
        assert tools == ()
        self.messages = messages
        content = messages[-1].content or ""
        plan_json = content.split("安全基础计划：", maxsplit=1)[1]
        return LLMToolCompletion(
            content=plan_json,
            tool_calls=(),
            provider=self.name,
            model=self.model,
        )

    def complete(self, prompt: str) -> LLMCompletion:
        """
        返回不使用的普通补全结果。

        :param prompt: 普通补全提示词。
        :return: 固定的补全结果。
        """
        return LLMCompletion(
            content=prompt,
            provider=self.name,
            model=self.model,
        )


async def _assert_plan_creation_forces_long_term_memory_context() -> None:
    """
    验证初始计划生成由后端强制查询并传入长期记忆。

    :return: 无返回值。
    """
    memories = MemoryRepositoryStub()
    llm = RecordingLLMProvider()
    use_cases = ProposalUseCases(
        profiles=ProfileRepositoryStub(),
        proposals=ProposalRepositoryStub(),
        plans=object(),
        memories=memories,
        llm=llm,
    )

    proposal = await use_cases.create_training_plan("memory-plan-user")

    model_context = "\n".join(
        message.content or "" for message in llm.messages
    )
    assert memories.requested_user_ids == ["memory-plan-user"]
    assert (
        "[preferred_equipment] 训练时只使用哑铃，不使用固定器械。"
        in model_context
    )
    assert "已参考 1 条长期记忆" in proposal.plan.goal_summary
    assert proposal.safety_check.valid is True


def test_plan_creation_forces_long_term_memory_context() -> None:
    """
    验证计划生成不依赖模型主动调用长期记忆工具。

    :return: 无返回值。
    """
    asyncio.run(_assert_plan_creation_forces_long_term_memory_context())
