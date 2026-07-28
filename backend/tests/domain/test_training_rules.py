from app.domain.models import ExercisePrescription, TrainingPlanDraft, WorkoutDayDraft
from app.domain.training_rules import validate_beginner_plan


def exercise(name: str, *, sets: int = 3, rpe: float = 7) -> ExercisePrescription:
    return ExercisePrescription(
        exercise_name=name,
        sets=sets,
        reps_min=8,
        reps_max=12,
        target_rpe=rpe,
    )


def test_beginner_plan_accepts_safe_three_day_plan():
    plan = TrainingPlanDraft(
        days=[
            WorkoutDayDraft(name="Day 1", exercises=[exercise("Leg Press")] * 4),
            WorkoutDayDraft(name="Day 2", exercises=[exercise("Chest Press")] * 4),
            WorkoutDayDraft(name="Day 3", exercises=[exercise("Lat Pulldown")] * 4),
        ]
    )

    result = validate_beginner_plan(plan)

    assert result["valid"] is True
    assert result["violations"] == []


def test_beginner_plan_rejects_excessive_rpe_and_exercise_count():
    plan = TrainingPlanDraft(
        days=[
            WorkoutDayDraft(
                name="Day 1",
                exercises=[exercise("Hard Set", rpe=9)] * 8,
            )
        ]
    )

    result = validate_beginner_plan(plan)

    assert result["valid"] is False
    assert {item["code"] for item in result["violations"]} == {
        "invalid_day_count",
        "too_many_exercises",
        "rpe_too_high",
    }
