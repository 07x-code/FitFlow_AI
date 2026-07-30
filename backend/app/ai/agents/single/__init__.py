"""单 Agent 能力入口。"""

from app.ai.agents.single.coach import CoachAgent, create_coach_agent
from app.ai.agents.single.planner import (
    TrainingPlanAgent,
    create_training_plan_agent,
)

__all__ = [
    "CoachAgent",
    "TrainingPlanAgent",
    "create_coach_agent",
    "create_training_plan_agent",
]
