from app.domain.models import FitnessProfileCreate


BLOCKING_FLAGS = {"chest_pain", "acute_injury"}


def assess_risk(profile: FitnessProfileCreate) -> dict[str, str | bool]:
    if any(flag in BLOCKING_FLAGS for flag in profile.health_flags):
        return {
            "level": "blocked",
            "can_auto_plan": False,
        }

    return {
        "level": "low",
        "can_auto_plan": True,
    }
