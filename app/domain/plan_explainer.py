from app.domain.models import (
    TrainingPlanExplanationResponse,
    TrainingPlanHistoryItem,
)


def explain_training_plan(plan: TrainingPlanHistoryItem) -> TrainingPlanExplanationResponse:
    day_count = len(plan.plan.days)
    exercise_counts = [len(day.exercises) for day in plan.plan.days]
    max_rpe = max(
        exercise.target_rpe
        for day in plan.plan.days
        for exercise in day.exercises
    )

    return TrainingPlanExplanationResponse(
        plan_id=plan.id,
        summary=f"这是一个每周 {day_count} 天的新手全身训练计划。",
        reasons=[
            f"训练天数来自你的用户画像，每周 {day_count} 天。",
            _explain_exercise_count(exercise_counts),
            f"所有动作的目标 RPE 都不超过 8，当前计划使用 RPE {max_rpe:g}。",
        ],
        safety_notes=[
            "如果出现胸痛、急性疼痛或明显不适，应停止训练并咨询专业人士。",
            "这个解释来自后端规则，后续可以交给大模型润色，但不能绕过安全规则。",
        ],
    )


def _explain_exercise_count(exercise_counts: list[int]) -> str:
    min_count = min(exercise_counts)
    max_count = max(exercise_counts)

    if min_count == max_count:
        return f"每天安排 {min_count} 个动作，符合新手安全范围。"

    return f"每天安排 {min_count} 到 {max_count} 个动作，符合新手安全范围。"
