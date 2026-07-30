"""兼容旧导入路径；新代码使用 :mod:`app.ai.core.message`。"""

from app.ai.core.message import AgentMessage, MessageRole

__all__ = ["AgentMessage", "MessageRole"]
