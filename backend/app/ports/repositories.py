from typing import Protocol

from app.domain.models import (
    FitnessProfileCreate,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanHistoryItem,
    TrainingPlanProposalResponse,
    UserMemoryCreate,
    UserMemoryResponse,
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
)


class ProfileRepositoryPort(Protocol):
    """用户健身画像持久化端口。"""

    def save(self, user_id: str, profile: FitnessProfileCreate) -> None:
        """
        保存用户健身画像。

        :param user_id: 用户标识。
        :param profile: 已校验的健身画像。
        :return: 无返回值。
        """

    def get(self, user_id: str) -> FitnessProfileCreate | None:
        """
        查询用户健身画像。

        :param user_id: 用户标识。
        :return: 用户健身画像；不存在时返回 None。
        """


class TrainingPlanRepositoryPort(Protocol):
    """训练计划持久化端口。"""

    def save(
        self,
        user_id: str,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanHistoryItem:
        """
        保存已通过安全检查的训练计划。

        :param user_id: 用户标识。
        :param plan: 训练计划。
        :param safety_check: 安全检查结果。
        :return: 已保存的训练计划。
        """

    def list_by_user(self, user_id: str) -> list[TrainingPlanHistoryItem]:
        """
        查询用户的训练计划历史。

        :param user_id: 用户标识。
        :return: 按时间倒序排列的训练计划列表。
        """

    def get_by_id_for_user(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanHistoryItem | None:
        """
        按用户和计划标识查询训练计划。

        :param user_id: 用户标识。
        :param plan_id: 训练计划标识。
        :return: 训练计划；不存在或不属于该用户时返回 None。
        """


class UserMemoryRepositoryPort(Protocol):
    """用户长期记忆持久化端口。"""

    def create(
        self,
        user_id: str,
        memory: UserMemoryCreate,
    ) -> UserMemoryResponse:
        """
        创建用户长期记忆。

        :param user_id: 用户标识。
        :param memory: 待保存的记忆。
        :return: 已保存的记忆。
        """

    def list_by_user(self, user_id: str) -> list[UserMemoryResponse]:
        """
        查询用户长期记忆。

        :param user_id: 用户标识。
        :return: 用户长期记忆列表。
        """

    def delete_by_id_for_user(self, user_id: str, memory_id: int) -> bool:
        """
        删除属于指定用户的长期记忆。

        :param user_id: 用户标识。
        :param memory_id: 记忆标识。
        :return: 是否成功删除。
        """


class TrainingPlanProposalRepositoryPort(Protocol):
    """训练计划提案持久化端口。"""

    def create(
        self,
        user_id: str,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanProposalResponse:
        """
        创建待确认的训练计划提案。

        :param user_id: 用户标识。
        :param plan: 训练计划。
        :param safety_check: 安全检查结果。
        :return: 已创建的提案。
        """

    def list_by_user(self, user_id: str) -> list[TrainingPlanProposalResponse]:
        """
        查询用户的提案列表。

        :param user_id: 用户标识。
        :return: 用户提案列表。
        """

    def get_by_id_for_user(
        self,
        user_id: str,
        proposal_id: int,
    ) -> TrainingPlanProposalResponse | None:
        """
        按用户和提案标识查询提案。

        :param user_id: 用户标识。
        :param proposal_id: 提案标识。
        :return: 提案；不存在或不属于该用户时返回 None。
        """

    def approve(
        self,
        user_id: str,
        proposal_id: int,
        approved_plan_id: int,
        decision_note: str | None,
    ) -> TrainingPlanProposalResponse | None:
        """
        批准训练计划提案。

        :param user_id: 用户标识。
        :param proposal_id: 提案标识。
        :param approved_plan_id: 批准后生成的正式计划标识。
        :param decision_note: 用户决策备注。
        :return: 更新后的提案；提案不存在时返回 None。
        """

    def reject(
        self,
        user_id: str,
        proposal_id: int,
        decision_note: str | None,
    ) -> TrainingPlanProposalResponse | None:
        """
        拒绝训练计划提案。

        :param user_id: 用户标识。
        :param proposal_id: 提案标识。
        :param decision_note: 用户决策备注。
        :return: 更新后的提案；提案不存在时返回 None。
        """


class WorkoutSessionRepositoryPort(Protocol):
    """训练记录持久化端口。"""

    def save(
        self,
        user_id: str,
        plan_id: int,
        plan_day_name: str,
        session: WorkoutSessionCreate,
        safety_alert: WorkoutSafetyAlert | None,
    ) -> WorkoutSessionResponse:
        """
        保存一次训练记录。

        :param user_id: 用户标识。
        :param plan_id: 正式训练计划标识。
        :param plan_day_name: 计划训练日名称。
        :param session: 训练记录。
        :param safety_alert: 根据反馈生成的安全提醒。
        :return: 已保存的训练记录。
        """

    def list_by_user(
        self,
        user_id: str,
        plan_id: int | None = None,
    ) -> list[WorkoutSessionResponse]:
        """
        查询用户训练记录。

        :param user_id: 用户标识。
        :param plan_id: 可选的训练计划筛选条件。
        :return: 用户训练记录列表。
        """
