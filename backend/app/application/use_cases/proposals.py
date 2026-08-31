import asyncio
import json
import re
from dataclasses import dataclass
from datetime import date

from pydantic import ValidationError

from app.application.errors import ConflictError, NotFoundError, UnprocessableError
from app.domain.models import (
    ProposalDecision,
    ProposalDecisionRequest,
    ProposalRevisionRequest,
    ProposalListResponse,
    ProposalStatus,
    SafetyCheckResult,
    TrainingPlanProposalResponse,
    TrainingPlanDraft,
)
from app.domain.plan_generator import generate_beginner_plan
from app.domain.plan_schedule import get_next_week_start
from app.domain.risk_rules import assess_risk
from app.domain.training_rules import validate_beginner_plan
from app.ports.repositories import (
    ProfileRepositoryPort,
    TrainingPlanProposalRepositoryPort,
    TrainingPlanRepositoryPort,
)
from app.ports.llm import LLMMessage, LLMProvider
DEFAULT_PLAN_TIMEZONE = "Asia/Shanghai"

GOAL_LABELS = {
    "fat_loss": "减脂",
    "muscle_gain": "增肌",
    "general_fitness": "提升综合体能",
}

EXERCISE_NAME_LABELS = {
    "Goblet Squat": "高脚杯深蹲",
    "Chest Press": "器械推胸",
    "Seated Row": "坐姿划船",
    "Dumbbell Romanian Deadlift": "哑铃罗马尼亚硬拉",
    "Leg Press": "腿举",
    "Lat Pulldown": "高位下拉",
    "Dumbbell Shoulder Press": "哑铃肩推",
    "Glute Bridge": "臀桥",
    "Split Squat": "分腿蹲",
    "Incline Dumbbell Press": "上斜哑铃卧推",
    "Cable Row": "绳索划船",
    "Hamstring Curl": "腿弯举",
    "Step Up": "登台阶",
    "Assisted Pull Up": "辅助引体向上",
    "Push Up": "俯卧撑",
    "Cable Pallof Press": "绳索帕洛夫推举",
    "Flat Barbell Bench Press": "平板杠铃卧推",
    "Tricep Rope Pushdown": "绳索下压",
    "Skullcrushers": "仰卧臂屈伸",
    "Seated Dumbbell Shoulder Press": "坐姿哑铃肩推",
    "Lateral Raise": "侧平举",
    "Barbell Bicep Curl": "杠铃弯举",
    "Hammer Curl": "锤式弯举",
    "Pull Up": "引体向上",
    "Seated Cable Row": "坐姿绳索划船",
    "Face Pulls": "面拉",
}


@dataclass(frozen=True)
class ProposalUseCases:
    """训练计划提案应用用例。"""

    profiles: ProfileRepositoryPort
    proposals: TrainingPlanProposalRepositoryPort
    plans: TrainingPlanRepositoryPort
    llm: LLMProvider

    async def create_training_plan(
        self,
        user_id: str,
    ) -> TrainingPlanProposalResponse:
        """
        生成经过安全检查、等待用户确认的训练计划提案。

        :param user_id: 用户标识。
        :return: 待确认的训练计划提案。
        """
        profile = await self.profiles.get(user_id)
        if profile is None:
            raise NotFoundError("Profile not found.")

        risk = assess_risk(profile)
        if risk["can_auto_plan"] is False:
            raise ConflictError(
                {
                    "message": "Automatic plan generation is blocked.",
                    "risk": risk,
                }
            )

        week_start = get_next_week_start(date.today())
        plan = generate_beginner_plan(
            profile,
            week_start=week_start,
            timezone=DEFAULT_PLAN_TIMEZONE,
            goal_summary=(
                f"围绕 {GOAL_LABELS[profile.goal.value]}目标安排下周训练。"
            ),
        )
        safety_check = SafetyCheckResult.model_validate(
            validate_beginner_plan(plan)
        )
        if safety_check.valid is False:
            raise UnprocessableError(
                {
                    "message": "Generated proposal failed safety check.",
                    "safety_check": safety_check.model_dump(),
                }
            )
        return await self.proposals.create(user_id, plan, safety_check)

    async def revise(
        self,
        user_id: str,
        proposal_id: int,
        request: ProposalRevisionRequest,
    ) -> TrainingPlanProposalResponse:
        """
        根据用户反馈生成并保存下一版训练计划提案。

        :param user_id: 用户标识。
        :param proposal_id: 待修改的提案标识。
        :param request: 用户提交的修改意见。
        :return: 等待用户确认的新版本提案。
        """
        proposal = await self.get(user_id, proposal_id)
        if proposal.status not in {
            ProposalStatus.PENDING,
            ProposalStatus.APPROVED,
        }:
            raise ConflictError("当前提案状态不允许修改。")

        try:
            completion = await asyncio.to_thread(
                self.llm.complete_with_tools,
                _build_revision_messages(proposal.plan, request.feedback),
                (),
            )
        except RuntimeError as exc:
            raise UnprocessableError(
                "AI 暂时无法生成修改版，请稍后重试。"
            ) from exc
        revised_plan = _localize_revised_plan(
            _parse_revised_plan(completion.content)
        )
        if revised_plan.week_start != proposal.plan.week_start:
            raise UnprocessableError("修改后的计划不能改变目标自然周。")

        safety_check = SafetyCheckResult.model_validate(
            validate_beginner_plan(revised_plan)
        )
        if not safety_check.valid:
            raise UnprocessableError(
                {
                    "message": "修改后的计划未通过安全检查。",
                    "safety_check": safety_check.model_dump(),
                }
            )

        if proposal.status == ProposalStatus.PENDING:
            revised = await self.proposals.create_revision(
                user_id,
                proposal.id,
                revised_plan,
                safety_check,
            )
        else:
            if proposal.approved_plan_id is None:
                raise ConflictError("已批准提案没有关联正式训练计划。")
            revised = await self.proposals.create_replacement(
                user_id,
                proposal.approved_plan_id,
                revised_plan,
                safety_check,
            )

        if revised is None:
            raise ConflictError("训练计划修改未能完成，请刷新后重试。")
        return revised

    async def list(self, user_id: str) -> ProposalListResponse:
        """
        查询用户训练计划提案。

        :param user_id: 用户标识。
        :return: 用户提案列表响应。
        """
        return ProposalListResponse(
            proposals=await self.proposals.list_by_user(user_id)
        )

    async def get(
        self,
        user_id: str,
        proposal_id: int,
    ) -> TrainingPlanProposalResponse:
        """
        查询属于当前用户的训练计划提案。

        :param user_id: 用户标识。
        :param proposal_id: 提案标识。
        :return: 训练计划提案。
        """
        proposal = await self.proposals.get_by_id_for_user(user_id, proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal not found.")
        return proposal

    async def decide(
        self,
        user_id: str,
        proposal_id: int,
        request: ProposalDecisionRequest,
    ) -> TrainingPlanProposalResponse:
        """
        批准或拒绝训练计划 Proposal。

        :param user_id: 用户标识。
        :param proposal_id: Proposal 标识。
        :param request: 用户决策。
        :return: 更新后的 Proposal。
        """
        proposal = await self.get(user_id, proposal_id)
        if proposal.status != ProposalStatus.PENDING:
            raise ConflictError(
                "Proposal has already been decided."
            )

        if request.decision == ProposalDecision.REJECT:
            rejected = await self.proposals.reject(
                user_id=user_id,
                proposal_id=proposal_id,
                decision_note=request.decision_note,
            )
            if rejected is None:
                raise ConflictError(
                    "Proposal decision could not be completed."
                )

            return rejected

        approving = await self.proposals.mark_approving(
            user_id,
            proposal_id,
        )
        if approving is None:
            raise ConflictError(
                "Proposal approval is already in progress."
            )

        version = 1
        if approving.base_plan_id is not None:
            base_plan = await self.plans.get_by_id_for_user(
                user_id,
                approving.base_plan_id,
            )
            if base_plan is None:
                raise ConflictError(
                    "Base training plan is unavailable."
                )

            superseded = await self.plans.mark_superseded(
                user_id,
                base_plan.id,
            )
            if superseded is None:
                raise ConflictError(
                    "Base training plan cannot be replaced."
                )

            version = base_plan.version + 1

        approved_plan = await self.plans.save(
            user_id,
            approving.plan,
            approving.safety_check,
            source_proposal_id=approving.id,
            version=version,
        )

        approved = await self.proposals.approve(
            user_id=user_id,
            proposal_id=approving.id,
            approved_plan_id=approved_plan.id,
            decision_note=request.decision_note,
        )
        if approved is None:
            raise ConflictError(
                "Proposal approval could not be completed."
            )

        return approved


def _build_revision_messages(
    plan: TrainingPlanDraft,
    feedback: str,
) -> list[LLMMessage]:
    """
    构建训练计划修订使用的结构化模型消息。

    :param plan: 当前版本训练计划。
    :param feedback: 用户明确提出的修改意见。
    :return: 只要求返回计划 JSON 的模型消息。
    """
    return [
        LLMMessage(
            role="system",
            content=(
                "你是 FitFlow AI 训练计划编辑器。根据用户反馈修改给定计划，"
                "所有训练日名称、训练重点和动作名称都必须使用简体中文。"
                "保持 week_start、week_end 和 timezone 不变；每周安排 2 到 4 天，"
                "每个训练日 4 到 7 个动作，target_rpe 不得超过 8。"
                f"动作只能从以下中文名称中选择：{', '.join(EXERCISE_NAME_LABELS.values())}。"
                "只返回一个符合原 JSON 字段结构的 JSON 对象，不要使用 Markdown，"
                "不要添加解释或额外字段。"
            ),
        ),
        LLMMessage(
            role="user",
            content=(
                f"当前计划：{plan.model_dump_json()}\n"
                f"修改意见：{feedback}"
            ),
        ),
    ]


def _parse_revised_plan(content: str | None) -> TrainingPlanDraft:
    """
    从模型文本中解析并校验修订后的训练计划。

    :param content: 模型返回的计划 JSON 文本。
    :return: 通过字段校验的训练计划。
    """
    if not content:
        raise UnprocessableError("模型没有返回修改后的训练计划。")

    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        raise UnprocessableError("模型返回的训练计划不是有效 JSON。")

    try:
        payload = json.loads(content[start : end + 1])
        return TrainingPlanDraft.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise UnprocessableError("模型返回的训练计划字段不完整。") from exc


def _localize_revised_plan(plan: TrainingPlanDraft) -> TrainingPlanDraft:
    """
    将模型生成计划中的已知英文名称统一转换为中文。

    :param plan: 已完成字段校验的模型计划。
    :return: 训练日和动作名称均为中文的计划。
    """
    localized_days = []
    for day in plan.days:
        day_name = re.sub(r"Day\s*(\d+)", r"第 \1 天", day.name, flags=re.I)
        day_name = re.sub("Full Body", "全身训练", day_name, flags=re.I)
        day_name = re.sub(r"\bA\b", "（一）", day_name)
        day_name = re.sub(r"\bB\b", "（二）", day_name)
        day_name = re.sub(r"\bC\b", "（三）", day_name)
        day_name = re.sub(r"\bD\b", "（四）", day_name)

        exercises = []
        for exercise in day.exercises:
            exercise_name = EXERCISE_NAME_LABELS.get(
                exercise.exercise_name,
                exercise.exercise_name,
            )
            if re.search(r"[a-z]", exercise_name, flags=re.I):
                raise UnprocessableError(
                    f"动作“{exercise.exercise_name}”缺少中文名称，请重新生成。"
                )
            exercises.append(
                exercise.model_copy(
                    update={"exercise_name": exercise_name}
                )
            )

        if re.search(r"[a-z]", day_name, flags=re.I):
            raise UnprocessableError("训练日名称必须使用中文。")
        localized_days.append(
            day.model_copy(
                update={
                    "name": day_name,
                    "exercises": exercises,
                }
            )
        )

    goal_summary = plan.goal_summary
    for goal, label in GOAL_LABELS.items():
        goal_summary = goal_summary.replace(goal, label)
    return plan.model_copy(
        update={
            "goal_summary": goal_summary,
            "days": localized_days,
        }
    )
