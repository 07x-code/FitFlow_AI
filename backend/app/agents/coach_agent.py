"""兼容旧导入路径；新代码使用 :mod:`app.ai.agents.single.coach`。"""

from app.ai.agents.single.coach import (
    CoachAgent,
    CoachAgentInput,
    build_coach_chat_prompt,
    create_coach_agent,
)

__all__ = [
    "CoachAgent",
    "CoachAgentInput",
    "build_coach_chat_prompt",
    "create_coach_agent",
]
