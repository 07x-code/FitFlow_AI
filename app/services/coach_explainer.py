from typing import Protocol

from app.domain.models import TrainingPlanExplanationResponse, TrainingPlanHistoryItem
from app.domain.plan_explainer import explain_training_plan


class CoachExplainer(Protocol):
    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        """Explain a saved training plan without changing safety decisions."""


class RuleBasedCoachExplainer:
    def explain_training_plan(
        self,
        plan: TrainingPlanHistoryItem,
    ) -> TrainingPlanExplanationResponse:
        return explain_training_plan(plan)
