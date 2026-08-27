from datetime import date

from app.domain.models import FitnessGoal, FitnessProfileCreate, Sex
from app.domain.plan_generator import generate_beginner_plan


def test_generate_beginner_plan_uses_explicit_week_metadata() -> None:
    """
    验证计划生成器使用调用方提供的目标周信息。

    :return: 无返回值。
    """
    profile = FitnessProfileCreate(
        age=28,
        sex=Sex.MALE,
        height_cm=178,
        weight_kg=72,
        goal=FitnessGoal.MUSCLE_GAIN,
        sessions_per_week=3,
        session_minutes=60,
        health_flags=[],
    )

    plan = generate_beginner_plan(
        profile,
        week_start=date(2026, 8, 24),
        timezone="Asia/Shanghai",
        goal_summary="以提升基础力量为主。",
    )

    assert plan.week_start == date(2026, 8, 24)
    assert plan.week_end == date(2026, 8, 30)
    assert plan.timezone == "Asia/Shanghai"
    assert plan.goal_summary == "以提升基础力量为主。"
    assert len(plan.days) == 3

    assert [day.scheduled_date for day in plan.days] == [
        date(2026, 8, 24),
        date(2026, 8, 26),
        date(2026, 8, 28),
    ]
    assert all(day.focus == "全身基础力量" for day in plan.days)
    assert all(day.estimated_minutes == 60 for day in plan.days)