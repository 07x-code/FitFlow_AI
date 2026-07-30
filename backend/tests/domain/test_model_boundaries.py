import ast
from pathlib import Path

from app.domain import models
from app.domain.models.coach import CoachChatRequest
from app.domain.models.memory import UserMemoryCreate
from app.domain.models.plan import TrainingPlanDraft
from app.domain.models.profile import FitnessProfileCreate
from app.domain.models.proposal import TrainingPlanProposalResponse
from app.domain.models.report import WeeklyReportResponse
from app.domain.models.workout import WorkoutSessionCreate


DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "app" / "domain"
MODEL_ROOT = DOMAIN_ROOT / "models"


def test_legacy_models_module_was_replaced_by_package() -> None:
    assert not (DOMAIN_ROOT / "models.py").exists()
    assert (MODEL_ROOT / "__init__.py").is_file()


def test_model_groups_have_independent_modules() -> None:
    expected_modules = {
        "coach.py",
        "memory.py",
        "plan.py",
        "profile.py",
        "proposal.py",
        "report.py",
        "workout.py",
    }

    assert {
        path.name
        for path in MODEL_ROOT.glob("*.py")
        if path.name != "__init__.py"
    } == expected_modules


def test_compatibility_exports_reference_split_model_classes() -> None:
    assert models.FitnessProfileCreate is FitnessProfileCreate
    assert models.TrainingPlanDraft is TrainingPlanDraft
    assert models.TrainingPlanProposalResponse is TrainingPlanProposalResponse
    assert models.WorkoutSessionCreate is WorkoutSessionCreate
    assert models.UserMemoryCreate is UserMemoryCreate
    assert models.WeeklyReportResponse is WeeklyReportResponse
    assert models.CoachChatRequest is CoachChatRequest


def test_leaf_model_modules_do_not_depend_on_other_model_groups() -> None:
    leaf_modules = {
        "coach.py",
        "memory.py",
        "plan.py",
        "profile.py",
        "workout.py",
    }
    violations: list[str] = []

    for module_name in leaf_modules:
        path = MODEL_ROOT / module_name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("app.domain.models.")
            ):
                violations.append(f"{module_name}:{node.lineno}")

    assert violations == []
