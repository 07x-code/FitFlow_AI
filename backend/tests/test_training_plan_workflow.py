from app.domain.models import FitnessProfileCreate
from app.infrastructure.persistence.sqlite.profile_repository import ProfileRepository

from app.ai.agents.single.planner import create_training_plan_agent


def save_profile(
    profile_repository: ProfileRepository,
    user_id: str,
    *,
    health_flags: list[str] | None = None,
) -> None:
    profile_repository.save(
        user_id,
        FitnessProfileCreate(
            age=22,
            sex="male",
            height_cm=175,
            weight_kg=70,
            goal="muscle_gain",
            sessions_per_week=3,
            session_minutes=60,
            health_flags=health_flags or [],
        ),
    )


def test_training_plan_workflow_returns_validated_safe_draft(tmp_path):
    db_path = tmp_path / "fitflow.db"
    profile_repository = ProfileRepository(db_path)
    workflow = create_training_plan_agent(
        profile_repository=profile_repository,
    )
    user_id = "safe-workflow-user"
    save_profile(profile_repository, user_id)

    result = workflow.run(user_id)

    assert result.status_code == 201
    assert result.response is not None
    assert len(result.response.plan.days) == 3
    assert result.response.safety_check.valid is True


def test_training_plan_workflow_blocks_risky_profile_without_saving_history(tmp_path):
    db_path = tmp_path / "fitflow.db"
    profile_repository = ProfileRepository(db_path)
    workflow = create_training_plan_agent(
        profile_repository=profile_repository,
    )
    user_id = "risky-workflow-user"
    save_profile(profile_repository, user_id, health_flags=["chest_pain"])

    result = workflow.run(user_id)

    assert result.status_code == 409
    assert result.response is None
    assert result.error_detail == {
        "message": "Automatic plan generation is blocked.",
        "risk": {
            "level": "blocked",
            "can_auto_plan": False,
        },
    }
