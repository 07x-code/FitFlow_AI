from app.domain.models import FitnessGoal, FitnessProfileCreate, Sex


ACTIVITY_FACTOR = 1.375
GOAL_CALORIE_ADJUSTMENTS = {
    FitnessGoal.FAT_LOSS: -300,
    FitnessGoal.MUSCLE_GAIN: 250,
    FitnessGoal.GENERAL_FITNESS: 0,
}


def calculate_nutrition_targets(profile: FitnessProfileCreate) -> dict[str, int]:
    sex_adjustment = 5 if profile.sex is Sex.MALE else -161
    bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + sex_adjustment
    calorie_target = bmr * ACTIVITY_FACTOR + GOAL_CALORIE_ADJUSTMENTS[profile.goal]
    protein_target = profile.weight_kg * 1.6

    return {
        "bmr_kcal": round(bmr),
        "calorie_target_kcal": round(calorie_target),
        "protein_target_g": round(protein_target),
    }
