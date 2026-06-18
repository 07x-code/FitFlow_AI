from app.core.config import AppSettings
from app.domain.models import (
    ExercisePrescription,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanHistoryItem,
    WorkoutDayDraft,
)
from app.services.coach_explainer import (
    LLMCoachExplainer,
    RuleBasedCoachExplainer,
    create_coach_explainer,
)
from app.services.llm_provider import LLMCompletion


class CapturingLLMProvider:
    name = "dashscope"
    model = "qwen-test"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> LLMCompletion:
        self.prompts.append(prompt)
        return LLMCompletion(
            content="LLM 润色后的训练计划总结。",
            provider=self.name,
            model=self.model,
        )


def exercise(name: str) -> ExercisePrescription:
    return ExercisePrescription(
        exercise_name=name,
        sets=3,
        reps_min=8,
        reps_max=12,
        target_rpe=7,
    )


def plan_history_item() -> TrainingPlanHistoryItem:
    return TrainingPlanHistoryItem(
        id=1,
        plan=TrainingPlanDraft(
            days=[
                WorkoutDayDraft(
                    name="Day 1 - Full Body A",
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


def test_rule_based_coach_explainer_returns_plan_explanation():
    #测试规则解释器
    explanation = RuleBasedCoachExplainer().explain_training_plan(plan_history_item())

    assert explanation.plan_id == 1
    assert explanation.summary == "这是一个每周 1 天的新手全身训练计划。"
    assert explanation.reasons[0] == "训练天数来自你的用户画像，每周 1 天。"
    assert explanation.safety_notes[1] == (
        "这个解释来自后端规则，后续可以交给大模型润色，但不能绕过安全规则。"
    )


def test_llm_coach_explainer_polishes_summary_but_preserves_rule_facts():
    #测试 LLM 解释器的核心安全原则
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


def test_create_coach_explainer_uses_rule_based_explainer_for_fake_provider():
    #测试工厂函数
    explainer = create_coach_explainer(
        AppSettings(
            llm_provider="fake",
            dashscope_api_key=None,
            openai_api_key=None,
            dashscope_model="qwen-plus",
            dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    )

    assert isinstance(explainer, RuleBasedCoachExplainer)


def test_create_coach_explainer_uses_llm_explainer_for_dashscope_provider():
    explainer = create_coach_explainer(
        AppSettings(
            llm_provider="dashscope",
            dashscope_api_key="dashscope-test-key",
            openai_api_key=None,
            dashscope_model="qwen-plus",
            dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    )

    assert isinstance(explainer, LLMCoachExplainer)
