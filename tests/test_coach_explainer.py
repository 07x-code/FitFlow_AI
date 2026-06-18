from app.domain.models import (
    ExercisePrescription,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanHistoryItem,
    WorkoutDayDraft,
)
from app.services.coach_explainer import RuleBasedCoachExplainer


def exercise(name: str) -> ExercisePrescription:
    return ExercisePrescription(
        exercise_name=name,
        sets=3,
        reps_min=8,
        reps_max=12,
        target_rpe=7,
    )


def test_rule_based_coach_explainer_returns_plan_explanation():
    plan = TrainingPlanHistoryItem(
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

    explanation = RuleBasedCoachExplainer().explain_training_plan(plan)

    assert explanation.plan_id == 1
    assert explanation.summary == "这是一个每周 1 天的新手全身训练计划。"
    assert explanation.reasons[0] == "训练天数来自你的用户画像，每周 1 天。"
    assert explanation.safety_notes[1] == (
        "这个解释来自后端规则，后续可以交给大模型润色，但不能绕过安全规则。"
    )
