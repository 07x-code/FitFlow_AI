import pytest
from pydantic import ValidationError

from app.domain.models import FitnessProfileCreate


def test_profile_rejects_too_many_training_days():
    with pytest.raises(ValidationError):
        FitnessProfileCreate(
            age=22,
            sex="male",
            height_cm=175,
            weight_kg=70,
            goal="muscle_gain",
            sessions_per_week=8,
            session_minutes=60,
        )


def test_profile_rejects_unknown_goal():
    with pytest.raises(ValidationError):
        FitnessProfileCreate(
            age=22,
            sex="male",
            height_cm=175,
            weight_kg=70,
            goal="随便练练",
            sessions_per_week=3,
            session_minutes=60,
        )


def test_profile_rejects_unknown_sex():
    with pytest.raises(ValidationError):
        FitnessProfileCreate(
            age=22,
            sex="unknown",
            height_cm=175,
            weight_kg=70,
            goal="muscle_gain",
            sessions_per_week=3,
            session_minutes=60,
        )