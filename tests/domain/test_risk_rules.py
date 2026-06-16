from app.domain.models import FitnessProfileCreate
from app.domain.risk_rules import assess_risk


def test_chest_pain_blocks_automatic_planning():
    profile = FitnessProfileCreate(
        age=22,
        sex="male",
        height_cm=175,
        weight_kg=70,
        goal="muscle_gain",
        sessions_per_week=3,
        session_minutes=60,
        health_flags=["chest_pain"],
    )

    result = assess_risk(profile)

    assert result["level"] == "blocked"
    assert result["can_auto_plan"] is False


def test_acute_injury_blocks_automatic_planning():
    profile = FitnessProfileCreate(
        age=22,
        sex="male",
        height_cm=175,
        weight_kg=70,
        goal="muscle_gain",
        sessions_per_week=3,
        session_minutes=60,
        health_flags=["acute_injury"],
    )

    result = assess_risk(profile)

    assert result["level"] == "blocked"
    assert result["can_auto_plan"] is False
