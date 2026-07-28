from app.domain.models import FitnessProfileCreate
from app.domain.nutrition_rules import calculate_nutrition_targets


def test_muscle_gain_targets_use_mifflin_and_small_surplus():
    profile = FitnessProfileCreate(
        age=22,
        sex="male",
        height_cm=175,
        weight_kg=70,
        goal="muscle_gain",
        sessions_per_week=3,
        session_minutes=60,
    )

    result = calculate_nutrition_targets(profile)

    assert result["bmr_kcal"] == 1689
    assert result["calorie_target_kcal"] == 2572
    assert result["protein_target_g"] == 112
