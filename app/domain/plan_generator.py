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


def generate_beginner_plan(profile: FitnessProfileCreate) -> TrainingPlanDraft:
    return TrainingPlanDraft(
        days=[
            WorkoutDayDraft(
                name=day_name,
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
            for day_name, exercise_names in DAY_TEMPLATES[: profile.sessions_per_week]
        ]
    )
