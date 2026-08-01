"""可由 API、CLI 或任务队列复用的应用用例。"""

from app.application.use_cases.coach import CoachUseCases
from app.application.use_cases.memories import MemoryUseCases
from app.application.use_cases.profiles import ProfileUseCases
from app.application.use_cases.proposals import ProposalUseCases
from app.application.use_cases.reports import ReportUseCases
from app.application.use_cases.training_plans import TrainingPlanUseCases
from app.application.use_cases.working_memory import WorkingMemoryUseCases
from app.application.use_cases.workouts import WorkoutUseCases

__all__ = [
    "CoachUseCases",
    "MemoryUseCases",
    "ProfileUseCases",
    "ProposalUseCases",
    "ReportUseCases",
    "TrainingPlanUseCases",
    "WorkingMemoryUseCases",
    "WorkoutUseCases",
]
