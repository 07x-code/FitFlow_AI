from dataclasses import dataclass
from typing import Protocol

from app.core.config import AppSettings
from app.domain.models import TrainingPlanExplanationResponse, TrainingPlanHistoryItem
from app.domain.plan_explainer import explain_training_plan
from app.services.llm_provider import LLMProvider, create_llm_provider


class CoachExplainer(Protocol):
    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        """
        解释已保存的训练计划，但不改变任何安全判定。

        :param plan: 已保存且通过安全检查的训练计划。
        :return: 包含总结、设计原因和安全提示的计划解释。
        """


class RuleBasedCoachExplainer:
    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        return explain_training_plan(plan)


@dataclass(frozen=True)
class LLMCoachExplainer:
    rule_explainer: CoachExplainer
    llm_provider: LLMProvider

    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        rule_explanation = self.rule_explainer.explain_training_plan(plan)
        completion = self.llm_provider.complete(_build_polish_prompt(rule_explanation))

        return TrainingPlanExplanationResponse(
            plan_id=rule_explanation.plan_id,
            summary=completion.content.strip(),
            reasons=rule_explanation.reasons,
            safety_notes=rule_explanation.safety_notes,
        )


def create_coach_explainer(settings: AppSettings | None = None) -> CoachExplainer:
    llm_provider = create_llm_provider(settings)
    rule_explainer = RuleBasedCoachExplainer()

    if llm_provider.name == "fake":
        return rule_explainer

    return LLMCoachExplainer(
        rule_explainer=rule_explainer,
        llm_provider=llm_provider,
    )


def _build_polish_prompt(explanation: TrainingPlanExplanationResponse) -> str:
    reasons = "\n".join(f"- {reason}" for reason in explanation.reasons)
    safety_notes = "\n".join(f"- {note}" for note in explanation.safety_notes)

    return (
        "请把下面的训练计划解释润色成一句更自然、友好的中文总结。\n"
        "要求：只输出一句 summary，不要新增训练动作，不要修改训练天数，"
        "不要改变 RPE、安全提醒或任何安全结论。\n\n"
        f"原始 summary：{explanation.summary}\n\n"
        f"规则 reasons：\n{reasons}\n\n"
        f"安全 notes：\n{safety_notes}"
    )
