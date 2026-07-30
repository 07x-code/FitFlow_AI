"""兼容旧导入路径；新代码使用 :mod:`app.ai.core.agent`。"""

from app.ai.core.agent import Agent, AgentConfig

__all__ = ["Agent", "AgentConfig"]
