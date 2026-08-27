from datetime import date, timedelta
from app.domain.models import (
    ExercisePrescription,
    FitnessProfileCreate,
    TrainingPlanDraft,
    WorkoutDayDraft,
)


DAY_TEMPLATES: list[tuple[str, list[str]]] = [
    (
        "Day 1 - Full Body A",
        ["Goblet Squat", "Chest Press", "Seated Row", "Dumbbell Romanian Deadlift"],
    ),
    (
        "Day 2 - Full Body B",
        ["Leg Press", "Lat Pulldown", "Dumbbell Shoulder Press", "Glute Bridge"],
    ),
    (
        "Day 3 - Full Body C",
        ["Split Squat", "Incline Dumbbell Press", "Cable Row", "Hamstring Curl"],
    ),
    (
        "Day 4 - Full Body D",
        ["Step Up", "Assisted Pull Up", "Push Up", "Cable Pallof Press"],
    ),
]


def generate_beginner_plan(
    profile: FitnessProfileCreate,
    *,
    week_start: date,
    timezone: str,
    goal_summary: str,
) -> TrainingPlanDraft:
    """
    根据用户画像和明确的目标周信息生成新手训练计划。

    :param profile: 用户健身画像。
    :param week_start: 目标自然周的开始日期。
    :param timezone: 计划日期使用的时区。
    :param goal_summary: 本次计划的目标摘要。
    :return: 生成的新手训练计划草案。
    """
    return TrainingPlanDraft(
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
        timezone=timezone,
        goal_summary=goal_summary,
        days=[
            WorkoutDayDraft(
                scheduled_date=week_start + timedelta(
                    days=day_index * 2
                ),
                name=day_name,
                focus="全身基础力量",
                estimated_minutes=profile.session_minutes,
                exercises=[
                    ExercisePrescription(
                        exercise_name=exercise_name,
                        sets=3,
                        reps_min=8,
                        reps_max=12,
                        target_rpe=7,
                    )
                    for exercise_name in exercise_names
                ],
            )
            for day_index, (day_name, exercise_names) in enumerate(
                DAY_TEMPLATES[: profile.sessions_per_week]
            )
        ]
    )
