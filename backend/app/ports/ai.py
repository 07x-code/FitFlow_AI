from typing import Any, Protocol

from app.domain.models import (
    CoachChatRequest,
    CoachChatResponse,
    TrainingPlanDraftResponse,
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
)


class TrainingPlanAgentResultPort(Protocol):
    """训练计划 Agent 的应用层可见结果。"""

    status_code: int
    response: TrainingPlanDraftResponse | None
    error_detail: Any


class TrainingPlanAgentPort(Protocol):
    """训练计划 Agent 对应用层暴露的端口。"""

    async def run(
        self,
        agent_input: str,
        **kwargs: object,
    ) -> TrainingPlanAgentResultPort:
        """
        为指定用户执行训练计划生成流程。

        :param agent_input: 用户标识。
        :param kwargs: Agent 扩展参数。
        :return: 训练计划生成结果。
        """


class CoachAgentPort(Protocol):
    """AI 教练对应用层暴露的端口。"""

    async def chat(
        self,
        user_id: str,
        session_id: str,
        request: CoachChatRequest,
    ) -> CoachChatResponse | None:
        """
        处理一次 AI 教练对话。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param request: 教练对话请求。
        :return: 教练回复；用户画像不存在时返回 None。
        """


class TrainingPlanExplainerPort(Protocol):
    """训练计划解释能力端口。"""

    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        """
        解释一份已通过安全检查的训练计划。

        :param plan: 已保存的训练计划。
        :return: 训练计划解释。
        """
