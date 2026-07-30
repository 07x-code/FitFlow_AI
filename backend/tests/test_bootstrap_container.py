from app.bootstrap.container import create_container
from app.core.config import AppSettings
from app.domain.models import FitnessProfileCreate


def test_container_wires_shared_repositories_agents_and_use_cases(tmp_path):
    container = create_container(
        db_path=tmp_path / "fitflow.db",
        settings=AppSettings(
            llm_provider="fake",
            dashscope_api_key=None,
            openai_api_key=None,
            dashscope_model="qwen-plus",
            dashscope_base_url=(
                "https://dashscope.aliyuncs.com/compatible-mode/v1"
            ),
        ),
    )
    user_id = "container-user"

    container.profiles.create(
        user_id,
        FitnessProfileCreate(
            age=22,
            sex="male",
            height_cm=175,
            weight_kg=70,
            goal="muscle_gain",
            sessions_per_week=3,
            session_minutes=60,
            health_flags=[],
        ),
    )
    draft = container.training_plans.create_draft(user_id)
    history = container.training_plans.list_history(user_id)

    assert draft.safety_check.valid is True
    assert len(history.plans) == 1
    assert history.plans[0].plan == draft.plan
