from app.domain.plan_schedule import get_next_week_start
from datetime import date
import pytest
from pydantic import ValidationError

from app.domain.models import (
    ExercisePrescription,
    TrainingPlanDraft,
    WorkoutDayDraft,
)


def test_training_plan_draft_keeps_target_week_metadata() -> None:
    """
    验证训练计划草案保留目标周、时区和目标摘要。

    :return: 无返回值。
    """
    plan = TrainingPlanDraft(
        week_start=date(2026, 8, 24),
        week_end=date(2026, 8, 30),
        timezone="Asia/Shanghai",
        goal_summary="以提升基础力量为主，每周训练三次。",
        days=[
                WorkoutDayDraft(
                scheduled_date=date(2026, 8, 24),
                name="Day 1",
                focus="下肢与核心基础力量",
                estimated_minutes=60,
                exercises=[
                    ExercisePrescription(
                        exercise_name="Goblet Squat",
                        sets=3,
                        reps_min=8,
                        reps_max=12,
                        target_rpe=7,
                    )
                ],
            )
        ],
    )

    assert plan.week_start == date(2026, 8, 24)
    assert plan.week_end == date(2026, 8, 30)
    assert plan.timezone == "Asia/Shanghai"
    assert plan.goal_summary == "以提升基础力量为主，每周训练三次。"

    first_day = plan.days[0]

    assert first_day.scheduled_date == date(2026, 8, 24)
    assert first_day.focus == "下肢与核心基础力量"
    assert first_day.estimated_minutes == 60

def test_training_plan_draft_rejects_invalid_week_range() -> None:
    """
    验证训练计划草案拒绝不完整的目标自然周。

    :return: 无返回值。
    """
    with pytest.raises(ValidationError, match="week_end"):
        TrainingPlanDraft(
            week_start=date(2026, 8, 24),
            week_end=date(2026, 8, 29),
            timezone="Asia/Shanghai",
            goal_summary="以提升基础力量为主。",
            days=[
                WorkoutDayDraft(
                    name="Day 1",
                    scheduled_date=date(2026, 8, 24),
                    focus="下肢与核心基础力量",
                    estimated_minutes=60,
                    exercises=[
                        ExercisePrescription(
                            exercise_name="Goblet Squat",
                            sets=3,
                            reps_min=8,
                            reps_max=12,
                            target_rpe=7,
                        )
                    ],
                )
            ],
        )


def test_get_next_week_start_returns_next_monday() -> None:
    """
    验证下周开始日期始终是当前自然周之后的星期一。

    :return: 无返回值。
    """
    assert get_next_week_start(date(2026, 8, 19)) == date(2026, 8, 24)
    assert get_next_week_start(date(2026, 8, 24)) == date(2026, 8, 31)
    assert get_next_week_start(date(2026, 8, 30)) == date(2026, 8, 31)
    