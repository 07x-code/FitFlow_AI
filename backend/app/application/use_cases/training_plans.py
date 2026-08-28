from dataclasses import dataclass
from http import HTTPStatus

from app.application.errors import (
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    UnprocessableError,
)
from app.domain.models import (
    TrainingPlanDraftResponse,
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
    TrainingPlanHistoryResponse,
)
from app.ports.ai import TrainingPlanAgentPort, TrainingPlanExplainerPort
from app.ports.repositories import TrainingPlanRepositoryPort


@dataclass(frozen=True)
class TrainingPlanUseCases:
    """训练计划应用用例。"""

    repository: TrainingPlanRepositoryPort
    agent: TrainingPlanAgentPort
    explainer: TrainingPlanExplainerPort

    async def create_draft(self, user_id: str) -> TrainingPlanDraftResponse:
        """
        通过训练计划 Agent 生成并校验训练计划草案。

        :param user_id: 用户标识。
        :return: 训练计划草案与安全检查结果。
        """
        result = await self.agent.run(user_id)
        if result.response is not None:
            return result.response

        if result.status_code == HTTPStatus.NOT_FOUND:
            raise NotFoundError(result.error_detail)
        if result.status_code == HTTPStatus.CONFLICT:
            raise ConflictError(result.error_detail)
        if result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            raise UnprocessableError(result.error_detail)
        raise InvalidRequestError(result.error_detail)

    async def list_history(self, user_id: str) -> TrainingPlanHistoryResponse:
        """
        查询用户训练计划历史。

        :param user_id: 用户标识。
        :return: 训练计划历史响应。
        """
        return TrainingPlanHistoryResponse(
            plans=await self.repository.list_by_user(user_id)
        )

    async def get_detail(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanHistoryItem:
        """
        查询属于当前用户的训练计划。

        :param user_id: 用户标识。
        :param plan_id: 训练计划标识。
        :return: 训练计划详情。
        """
        plan = await self.repository.get_by_id_for_user(user_id, plan_id)
        if plan is None:
            raise NotFoundError("Training plan not found.")
        return plan

    async def explain(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanExplanationResponse:
        """
        解释属于当前用户的训练计划。

        :param user_id: 用户标识。
        :param plan_id: 训练计划标识。
        :return: 训练计划解释。
        """
        plan = await self.get_detail(user_id, plan_id)
        return self.explainer.explain_training_plan(plan)
