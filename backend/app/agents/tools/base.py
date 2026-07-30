"""兼容旧导入路径；新代码使用 :mod:`app.ai.tools.base`。"""

from app.ai.tools.base import FunctionTool, Tool, ToolParameter

__all__ = ["FunctionTool", "Tool", "ToolParameter"]
