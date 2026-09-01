from typing import Protocol
from datetime import datetime
from app.domain.models import (
    FitnessProfileCreate,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanHistoryItem,
    TrainingPlanProposalResponse,
    UserAccount,
    UserMemoryCreate,
    UserMemoryResponse,
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
)


UserAuthentication = tuple[UserAccount, str]


class DuplicateEmailError(Exception):
    """用户邮箱已经存在。"""


class UserRepositoryPort(Protocol):
    """用户账号持久化端口。"""

    async def create(
        self,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> UserAccount:
        """
        创建用户账号。

        :param email: 用户邮箱。
        :param password_hash: Argon2id 密码哈希。
        :param display_name: 用户显示名称。
        :return: 已创建的安全用户账号。
        """
        ...

    async def get_by_id(self, user_id: str) -> UserAccount | None:
        """
        按用户标识查询账号。

        :param user_id: 用户标识。
        :return: 用户账号；不存在时返回 None。
        """
        ...

    async def get_by_email(self, email: str) -> UserAccount | None:
        """
        按规范化邮箱查询账号。

        :param email: 用户输入的邮箱。
        :return: 用户账号；不存在时返回 None。
        """
        ...

    async def get_authentication_by_email(
        self,
        email: str,
    ) -> UserAuthentication | None:
        """
        查询登录验证需要的用户账号和密码哈希。

        :param email: 用户输入的邮箱。
        :return: 用户账号与密码哈希；不存在时返回 None。
        """
        ...

    async def mark_login(self, user_id: str) -> UserAccount | None:
        """
        记录用户最近登录时间。

        :param user_id: 用户标识。
        :return: 更新后的用户账号；不存在时返回 None。
        """
        ...

    async def disable(self, user_id: str) -> UserAccount | None:
        """
        禁用用户账号。

        :param user_id: 用户标识。
        :return: 更新后的用户账号；不存在时返回 None。
        """
        ...


class ProfileRepositoryPort(Protocol):
    """用户健身画像持久化端口。"""

    async def save(self, user_id: str, profile: FitnessProfileCreate) -> None:
        """
        保存用户健身画像。

        :param user_id: 用户标识。
        :param profile: 已校验的健身画像。
        :return: 无返回值。
        """
        ...

    async def get(self, user_id: str) -> FitnessProfileCreate | None:
        """
        查询用户健身画像。

        :param user_id: 用户标识。
        :return: 用户健身画像；不存在时返回 None。
        """
        ...


class TrainingPlanRepositoryPort(Protocol):
    """正式训练计划持久化端口。"""

    async def save(
        self,
        user_id: str,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
        *,
        source_proposal_id: int,
        version: int,
    ) -> TrainingPlanHistoryItem:
        """
        保存由已批准 Proposal 生成的正式训练计划。

        :param user_id: 用户标识。
        :param plan: 已通过校验的训练计划草案。
        :param safety_check: 确定性安全检查结果。
        :param source_proposal_id: 来源 Proposal 标识。
        :param version: 同一用户同一周的计划版本。
        :return: 已保存的正式训练计划。
        """
        ...

    async def list_by_user(
        self,
        user_id: str,
    ) -> list[TrainingPlanHistoryItem]:
        """
        查询用户的正式训练计划历史。

        :param user_id: 用户标识。
        :return: 按时间倒序排列的正式训练计划列表。
        """
        ...

    async def get_by_id_for_user(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanHistoryItem | None:
        """
        按用户和计划标识查询正式训练计划。

        :param user_id: 用户标识。
        :param plan_id: 正式训练计划标识。
        :return: 正式训练计划；不存在或不属于该用户时返回 None。
        """
        ...

    async def mark_superseded(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanHistoryItem | None:
        """
        将用户当前正式计划更新为已被替换。

        :param user_id: 用户标识。
        :param plan_id: 正式训练计划标识。
        :return: 更新后的正式计划；当前状态不允许更新时返回 None。
        """
        ...

class UserMemoryRepositoryPort(Protocol):
    """用户长期记忆持久化端口。"""

    async def create(
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
        ...

    async def list_by_user(
            self,
            user_id: str
    ) -> list[UserMemoryResponse]:
        """
        查询用户长期记忆。

        :param user_id: 用户标识。
        :return: 用户长期记忆列表。
        """
        ...

    async def upsert_by_key(
        self,
        user_id: str,
        memory: UserMemoryCreate,
    ) -> UserMemoryResponse | None:
        """
        按规范化键新增或更新一条 active 长期记忆。

        :param user_id: 用户标识。
        :param memory: 包含规范化键的长期记忆。
        :return: 发生新增或内容更新时返回记忆；内容未变化时返回 None。
        """
        ...

    async def forget_by_key(
        self,
        user_id: str,
        memory_type: str,
        memory_key: str,
    ) -> UserMemoryResponse | None:
        """
        按规范化键软删除一条 active 长期记忆。

        :param user_id: 用户标识。
        :param memory_type: 长期记忆类型。
        :param memory_key: 规范化记忆键。
        :return: 已停用的记忆；不存在时返回 None。
        """
        ...

    async def delete_by_id_for_user(self, user_id: str, memory_id: int) -> bool:
        """
        删除属于指定用户的长期记忆。

        :param user_id: 用户标识。
        :param memory_id: 记忆标识。
        :return: 是否成功删除。
        """
        ...


class TrainingPlanProposalRepositoryPort(Protocol):
    """训练计划提案持久化端口。"""

    async def create(
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
        ...

    async def list_by_user(self, user_id: str) -> list[TrainingPlanProposalResponse]:
        """
        查询用户的提案列表。

        :param user_id: 用户标识。
        :return: 用户提案列表。
        """
        ...

    async def get_by_id_for_user(
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
        ...

    async def approve(
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
        ...

    async def reject(
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
        ...

    async def mark_approving(
        self,
        user_id: str,
        proposal_id: int,
    ) -> TrainingPlanProposalResponse | None:
        """
        将待决定 Proposal 原子更新为批准处理中。

        :param user_id: 用户标识。
        :param proposal_id: Proposal 标识。
        :return: 更新后的 Proposal；当前状态不允许更新时返回 None。
        """
        ...

    async def create_revision(
        self,
        user_id: str,
        parent_proposal_id: int,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanProposalResponse | None:
        """
        根据待决定 Proposal 创建下一版修订。

        :param user_id: 用户标识。
        :param parent_proposal_id: 被修订的 Proposal 标识。
        :param plan: 修订后的训练计划草案。
        :param safety_check: 修订计划的确定性安全检查结果。
        :return: 新版本 Proposal；原 Proposal 不可修订时返回 None。
        """
        ...

    async def create_replacement(
        self,
        user_id: str,
        base_plan_id: int,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanProposalResponse | None:
        """
        基于用户已有正式计划创建替换 Proposal。

        :param user_id: 用户标识。
        :param base_plan_id: 被替换的正式计划标识。
        :param plan: 替换后的训练计划草案。
        :param safety_check: 替换计划的确定性安全检查结果。
        :return: 替换 Proposal；基础计划不匹配时返回 None。
        """
        ...


class WorkoutSessionRepositoryPort(Protocol):
    """训练记录持久化端口。"""

    async def save(
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
        ...

    async def list_by_user(
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
        ...
    async def list_by_user_in_period(
        self,
        user_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WorkoutSessionResponse]:
        """
        查询指定用户在时间区间内创建的训练记录。

        :param user_id: 用户标识。
        :param start_at: 包含在查询范围内的起始时间。
        :param end_at: 不包含在查询范围内的结束时间。
        :return: 时间区间内的训练记录列表。
        """
        ...
