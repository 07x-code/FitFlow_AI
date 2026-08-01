from app.ai.agents.single.coach import create_coach_agent
from app.ai.tools.fitness import (
    ASSESS_RISK_TOOL,
    GENERATE_TRAINING_PLAN_TOOL,
    GET_PROFILE_TOOL,
    SAVE_TRAINING_PLAN_TOOL,
    VALIDATE_TRAINING_PLAN_TOOL,
)
from app.ai.agents.single.planner import create_training_plan_agent
from app.domain.models import CoachChatRequest, FitnessProfileCreate
from app.infrastructure.memory.in_memory import InMemoryWorkingMemoryStore
from app.infrastructure.persistence.sqlite.profile_repository import ProfileRepository
from app.infrastructure.persistence.sqlite.training_plan_repository import TrainingPlanRepository
from app.infrastructure.persistence.sqlite.user_memory_repository import UserMemoryRepository
from app.infrastructure.knowledge.retriever import KnowledgeRetriever
from app.infrastructure.llm.provider import FakeLLMProvider


def build_profile(*, health_flags: list[str] | None = None) -> FitnessProfileCreate:
    return FitnessProfileCreate(
        age=22,
        sex="male",
        height_cm=175,
        weight_kg=70,
        goal="muscle_gain",
        sessions_per_week=3,
        session_minutes=60,
        health_flags=health_flags or [],
    )


def test_training_plan_agent_exposes_deterministic_steps_as_tools(tmp_path):
    db_path = tmp_path / "fitflow.db"
    agent = create_training_plan_agent(
        profile_repository=ProfileRepository(db_path),
        training_plan_repository=TrainingPlanRepository(db_path),
    )

    assert agent.tool_registry.names() == (
        GET_PROFILE_TOOL,
        ASSESS_RISK_TOOL,
        GENERATE_TRAINING_PLAN_TOOL,
        VALIDATE_TRAINING_PLAN_TOOL,
        SAVE_TRAINING_PLAN_TOOL,
    )


def test_training_plan_agent_runs_and_persists_a_safe_plan(tmp_path):
    db_path = tmp_path / "fitflow.db"
    profiles = ProfileRepository(db_path)
    plans = TrainingPlanRepository(db_path)
    profiles.save("safe-user", build_profile())
    agent = create_training_plan_agent(
        profile_repository=profiles,
        training_plan_repository=plans,
    )

    result = agent.run("safe-user")

    assert result.status_code == 201
    assert result.response is not None
    assert result.response.safety_check.valid is True
    assert len(plans.list_by_user("safe-user")) == 1


def test_coach_agent_uses_tools_but_keeps_llm_out_of_blocked_path(tmp_path):
    db_path = tmp_path / "fitflow.db"
    profiles = ProfileRepository(db_path)
    plans = TrainingPlanRepository(db_path)
    working_memory = InMemoryWorkingMemoryStore()
    profiles.save("blocked-user", build_profile(health_flags=["chest_pain"]))
    agent = create_coach_agent(
        profile_repository=profiles,
        training_plan_repository=plans,
        memory_repository=UserMemoryRepository(db_path),
        knowledge_retriever=KnowledgeRetriever.from_default_file(),
        llm_provider=FakeLLMProvider(),
        working_memory=working_memory,
    )

    response = agent.chat(
        "blocked-user",
        "blocked-session",
        CoachChatRequest(message="Can I train today?"),
    )

    assert response is not None
    assert response.safety_level == "blocked"
    assert response.referenced_plan_id is None
    assert agent.get_history() == ()
    assert {
        item.kind for item in working_memory.list("blocked-user", "blocked-session")
    } == {"message", "tool_observation"}
