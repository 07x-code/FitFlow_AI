from app.domain.models import TrainingPlanDraft


def validate_beginner_plan(plan: TrainingPlanDraft) -> dict[str, bool | list[dict[str, str]]]:
    violations: list[dict[str, str]] = []

    if not 2 <= len(plan.days) <= 4:
        violations.append(
            {
                "code": "invalid_day_count",
                "message": "新手训练计划每周应安排 2 到 4 天。",
            }
        )

    for day in plan.days:
        if not 4 <= len(day.exercises) <= 7:
            violations.append(
                {
                    "code": "too_many_exercises",
                    "message": f"{day.name} 应包含 4 到 7 个动作。",
                }
            )

        if any(exercise.target_rpe > 8 for exercise in day.exercises):
            violations.append(
                {
                    "code": "rpe_too_high",
                    "message": f"{day.name} 包含目标 RPE 高于 8 的动作。",
                }
            )

    return {
        "valid": len(violations) == 0,
        "violations": violations,
    }
