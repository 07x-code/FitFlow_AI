from dataclasses import dataclass

from app.domain.models import (
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
)
from app.domain.plan_explainer import explain_training_plan
from app.ports.ai import TrainingPlanExplainerPort
from app.ports.llm import LLMProvider


class RuleBasedCoachExplainer:
    """使用确定性领域规则解释训练计划。"""

    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        """
        使用领域规则解释已保存的训练计划。

        :param plan: 已保存且通过安全检查的训练计划。
        :return: 包含总结、设计原因和安全提示的计划解释。
        """
        return explain_training_plan(plan)


@dataclass(frozen=True)
class LLMCoachExplainer:
    """只允许大模型润色规则解释总结的计划解释器。"""

    rule_explainer: TrainingPlanExplainerPort
    llm_provider: LLMProvider

    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        """
        润色规则总结，同时保留规则生成的事实和安全提示。

        :param plan: 已保存且通过安全检查的训练计划。
        :return: 总结经过润色但安全事实不变的计划解释。
        """
        rule_explanation = self.rule_explainer.explain_training_plan(plan)
        completion = self.llm_provider.complete(
            _build_polish_prompt(rule_explanation)
        )

        return TrainingPlanExplanationResponse(
            plan_id=rule_explanation.plan_id,
            summary=completion.content.strip(),
            reasons=rule_explanation.reasons,
            safety_notes=rule_explanation.safety_notes,
        )


def create_training_plan_explainer(
    llm_provider: LLMProvider,
) -> TrainingPlanExplainerPort:
    """
    根据已装配的大模型 Provider 创建训练计划解释器。

    :param llm_provider: 已由基础设施层创建的大模型 Provider。
    :return: 规则解释器或带大模型润色能力的解释器。
    """
    rule_explainer = RuleBasedCoachExplainer()
    if llm_provider.name == "fake":
        return rule_explainer

    return LLMCoachExplainer(
        rule_explainer=rule_explainer,
        llm_provider=llm_provider,
    )


def _build_polish_prompt(
    explanation: TrainingPlanExplanationResponse,
) -> str:
    """
    构建只允许润色总结的安全提示词。

    :param explanation: 领域规则生成的训练计划解释。
    :return: 交给大模型的润色提示词。
    """
    reasons = "\n".join(f"- {reason}" for reason in explanation.reasons)
    safety_notes = "\n".join(
        f"- {note}" for note in explanation.safety_notes
    )

    return (
        "请把下面的训练计划解释润色成一句更自然、友好的中文总结。\n"
        "要求：只输出一句 summary，不要新增训练动作，不要修改训练天数，"
        "不要改变 RPE、安全提醒或任何安全结论。\n\n"
        f"原始 summary：{explanation.summary}\n\n"
        f"规则 reasons：\n{reasons}\n\n"
        f"安全 notes：\n{safety_notes}"
    )
