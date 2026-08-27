from datetime import date
from app.ai.services.training_plan_explainer import (
    LLMCoachExplainer,
    RuleBasedCoachExplainer,
    create_training_plan_explainer,
)
from app.domain.models import (
    ExercisePrescription,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanHistoryItem,
    TrainingPlanStatus,
    WorkoutDayDraft,
)
from app.infrastructure.llm.provider import FakeLLMProvider
from app.ports.llm import LLMCompletion


class CapturingLLMProvider:
    """记录提示词的测试用大模型 Provider。"""

    name = "dashscope"
    model = "qwen-test"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> LLMCompletion:
        """
        记录提示词并返回固定回复。

        :param prompt: 待记录的大模型提示词。
        :return: 固定的测试回复。
        """
        self.prompts.append(prompt)
        return LLMCompletion(
            content="LLM 润色后的训练计划总结。",
            provider=self.name,
            model=self.model,
        )


def exercise(name: str) -> ExercisePrescription:
    """
    创建测试使用的训练动作。

    :param name: 动作名称。
    :return: 固定训练参数的动作处方。
    """
    return ExercisePrescription(
        exercise_name=name,
        sets=3,
        reps_min=8,
        reps_max=12,
        target_rpe=7,
    )


def plan_history_item() -> TrainingPlanHistoryItem:
    """
    创建测试使用的已保存训练计划。

    :return: 已通过安全校验的训练计划记录。
    """
    return TrainingPlanHistoryItem(
        id=1,
        version=2,
        status=TrainingPlanStatus.ACTIVE,
        source_proposal_id=42,
        plan=TrainingPlanDraft(
            week_start=date(2026, 8, 24),
            week_end=date(2026, 8, 30),
            timezone="Asia/Shanghai",
            goal_summary="每周一次的新手全身训练计划。",
            days=[
                WorkoutDayDraft(
                    scheduled_date=date(2026, 8, 24),
                    name="Day 1 - Full Body A",
                    focus="全身基础力量",
                    estimated_minutes=60,
                    exercises=[
                        exercise("Goblet Squat"),
                        exercise("Chest Press"),
                        exercise("Seated Row"),
                        exercise("Dumbbell Romanian Deadlift"),
                    ],
                )
            ]
        ),
        safety_check=SafetyCheckResult(valid=True, violations=[]),
        created_at="2026-06-18 16:00:00",
    )


def test_training_plan_history_keeps_formal_plan_metadata() -> None:
    """
    验证正式训练计划保留版本、状态和来源 Proposal。

    :return: 无返回值。
    """
    item = plan_history_item()

    assert item.version == 2
    assert item.status == TrainingPlanStatus.ACTIVE
    assert item.source_proposal_id == 42


def test_rule_based_coach_explainer_returns_plan_explanation():
    explanation = RuleBasedCoachExplainer().explain_training_plan(
        plan_history_item()
    )

    assert explanation.plan_id == 1
    assert explanation.summary == "这是一个每周 1 天的新手全身训练计划。"
    assert explanation.reasons[0] == "训练天数来自你的用户画像，每周 1 天。"
    assert explanation.safety_notes[1] == (
        "这个解释来自后端规则，后续可以交给大模型润色，但不能绕过安全规则。"
    )


def test_llm_coach_explainer_polishes_summary_but_preserves_rule_facts():
    plan = plan_history_item()
    rule_explainer = RuleBasedCoachExplainer()
    rule_explanation = rule_explainer.explain_training_plan(plan)
    llm_provider = CapturingLLMProvider()

    explanation = LLMCoachExplainer(
        rule_explainer=rule_explainer,
        llm_provider=llm_provider,
    ).explain_training_plan(plan)

    assert explanation.plan_id == rule_explanation.plan_id
    assert explanation.summary == "LLM 润色后的训练计划总结。"
    assert explanation.reasons == rule_explanation.reasons
    assert explanation.safety_notes == rule_explanation.safety_notes
    assert len(llm_provider.prompts) == 1
    assert rule_explanation.summary in llm_provider.prompts[0]
    assert "不要新增训练动作" in llm_provider.prompts[0]


def test_factory_uses_rule_based_explainer_for_fake_provider():
    explainer = create_training_plan_explainer(FakeLLMProvider())

    assert isinstance(explainer, RuleBasedCoachExplainer)


def test_factory_uses_llm_explainer_for_online_provider():
    explainer = create_training_plan_explainer(CapturingLLMProvider())

    assert isinstance(explainer, LLMCoachExplainer)
