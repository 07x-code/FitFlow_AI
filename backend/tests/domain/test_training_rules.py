from datetime import date
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
        week_start=date(2026, 8, 24),
        week_end=date(2026, 8, 30),
        timezone="Asia/Shanghai",
        goal_summary="用于验证新手训练安全规则。",
        days=[
            WorkoutDayDraft(
                scheduled_date=date(2026, 8, 24),
                name="Day 1",
                focus="下肢训练",
                estimated_minutes=60,
                exercises=[exercise("Leg Press")] * 4,
            ),
            WorkoutDayDraft(
                scheduled_date=date(2026, 8, 26),
                name="Day 2",
                focus="上肢推举",
                estimated_minutes=60,
                exercises=[exercise("Chest Press")] * 4,
            ),
            WorkoutDayDraft(
                scheduled_date=date(2026, 8, 28),
                name="Day 3",
                focus="上肢拉力",
                estimated_minutes=60,
                exercises=[exercise("Lat Pulldown")] * 4,
            ),
        ]
    )

    result = validate_beginner_plan(plan)

    assert result["valid"] is True
    assert result["violations"] == []


def test_beginner_plan_rejects_excessive_rpe_and_exercise_count():
    plan = TrainingPlanDraft(
        week_start=date(2026, 8, 24),
        week_end=date(2026, 8, 30),
        timezone="Asia/Shanghai",
        goal_summary="用于验证新手训练安全规则。",
        days=[
            WorkoutDayDraft(
                name="Day 1",
                scheduled_date=date(2026, 8, 24),
                focus="高强度测试",
                estimated_minutes=60,
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
