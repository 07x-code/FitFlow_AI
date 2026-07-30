"""兼容旧导入路径；新代码使用 :mod:`app.ai.agents.single.planner`。"""

from app.ai.agents.single.planner import (
    TrainingPlanAgent,
    TrainingPlanAgentResult,
    TrainingPlanAgentState,
    create_training_plan_agent,
)

__all__ = [
    "TrainingPlanAgent",
    "TrainingPlanAgentResult",
    "TrainingPlanAgentState",
    "create_training_plan_agent",
]
