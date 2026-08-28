import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.ai.tools.fitness import (
    GET_LATEST_TRAINING_PLAN_TOOL,
    RECALL_USER_MEMORY_TOOL,
    RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
    KnowledgeQuery,
)
from app.ai.tools.registry import ToolRegistry
from app.domain.models import (
    FitnessKnowledgeItem,
    TrainingPlanHistoryItem,
    UserMemoryResponse,
)
from app.ports.llm import LLMToolCall, LLMToolDefinition


class EmptyToolArguments(BaseModel):
    """不接收模型参数的工具输入。"""

    model_config = ConfigDict(extra="forbid")


class KnowledgeToolArguments(BaseModel):
    """健身知识检索工具的模型可见输入。"""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        min_length=1,
        max_length=500,
        description="需要从健身知识库检索的问题。",
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=5,
        description="最多返回的知识条目数量。",
    )


@dataclass(frozen=True)
class CoachToolRuntime:
    """不发送给大模型的 Coach 工具运行上下文。"""

    user_id: str
    session_id: str


@dataclass(frozen=True)
class CoachToolExecution:
    """一次 Coach 只读工具执行结果。"""

    tool_name: str
    content: str
    observation: str
    success: bool
    referenced_plan_id: int | None = None
    knowledge_items: tuple[FitnessKnowledgeItem, ...] = ()


class CoachReadOnlyToolExecutor:
    """对模型只暴露白名单只读工具并注入可信运行时上下文。"""

    def __init__(self, registry: ToolRegistry) -> None:
        """
        初始化 Coach 只读工具执行器。

        :param registry: 已装配 Repository 和知识检索器的工具注册表。
        :return: 无返回值。
        """
        self.registry = registry
        self._definitions = (
            LLMToolDefinition(
                name=GET_LATEST_TRAINING_PLAN_TOOL,
                description=(
                    "仅在问题涉及用户当前训练安排、训练日或计划原因时，"
                    "读取该用户最近的训练计划。"
                ),
                parameters=EmptyToolArguments.model_json_schema(),
            ),
            LLMToolDefinition(
                name=RECALL_USER_MEMORY_TOOL,
                description=(
                    "仅在问题涉及用户过去明确保存的偏好、限制或习惯时，"
                    "读取该用户的长期记忆。"
                ),
                parameters=EmptyToolArguments.model_json_schema(),
            ),
            LLMToolDefinition(
                name=RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
                description=(
                    "仅在回答需要健身动作、训练强度、热身、恢复或安全知识"
                    "依据时，检索本地健身知识库。"
                ),
                parameters=KnowledgeToolArguments.model_json_schema(),
            ),
        )

    def definitions(self) -> tuple[LLMToolDefinition, ...]:
        """
        返回提供给大模型的只读工具定义。

        :return: 不包含 user_id、session_id 或 Repository 的工具定义。
        """
        return self._definitions

    async def execute(
        self,
        call: LLMToolCall,
        runtime: CoachToolRuntime,
    ) -> CoachToolExecution:
        """
        校验并执行一次白名单只读工具调用。

        :param call: 大模型生成的结构化工具调用。
        :param runtime: 后端注入且不会发送给模型的可信上下文。
        :return: 可返回给模型的紧凑结果和内部观察摘要。
        """
        try:
            if call.name == GET_LATEST_TRAINING_PLAN_TOOL:
                EmptyToolArguments.model_validate(call.arguments)
                return await self._get_latest_plan(runtime)
            if call.name == RECALL_USER_MEMORY_TOOL:
                EmptyToolArguments.model_validate(call.arguments)
                return await self._recall_memories(runtime)
            if call.name == RETRIEVE_FITNESS_KNOWLEDGE_TOOL:
                arguments = KnowledgeToolArguments.model_validate(
                    call.arguments
                )
                return await self._retrieve_knowledge(arguments)
        except ValidationError as exc:
            return _error_execution(
                call.name,
                "invalid_arguments",
                details=exc.errors(include_url=False),
                observation="模型提交的工具参数未通过 Pydantic 校验。",
            )
        except Exception:
            return _error_execution(
                call.name,
                "tool_execution_failed",
                observation="只读工具执行失败，未向模型暴露内部异常。",
            )

        return _error_execution(
            call.name,
            "tool_not_allowed",
            observation="模型请求了白名单之外的工具，后端已拒绝执行。",
        )

    async def _get_latest_plan(
        self,
        runtime: CoachToolRuntime,
    ) -> CoachToolExecution:
        """
        使用后端注入的用户标识读取最近训练计划。

        :param runtime: 可信的工具运行上下文。
        :return: 最近训练计划的紧凑执行结果。
        """
        plan = await self.registry.execute_async(
            GET_LATEST_TRAINING_PLAN_TOOL,
            runtime.user_id,
        )
        if plan is None:
            return CoachToolExecution(
                tool_name=GET_LATEST_TRAINING_PLAN_TOOL,
                content=_json_content({"ok": True, "found": False}),
                observation="用户当前没有训练计划。",
                success=True,
            )

        latest_plan = TrainingPlanHistoryItem.model_validate(plan)
        payload = {
            "ok": True,
            "found": True,
            "plan_id": latest_plan.id,
            "created_at": latest_plan.created_at,
            "days": [
                day.model_dump(mode="json")
                for day in latest_plan.plan.days
            ],
            "safety_check_passed": latest_plan.safety_check.valid,
        }
        return CoachToolExecution(
            tool_name=GET_LATEST_TRAINING_PLAN_TOOL,
            content=_json_content(payload),
            observation=f"已按需读取训练计划 #{latest_plan.id}。",
            success=True,
            referenced_plan_id=latest_plan.id,
        )

    async def _recall_memories(
        self,
        runtime: CoachToolRuntime,
    ) -> CoachToolExecution:
        """
        使用后端注入的用户标识读取长期记忆。

        :param runtime: 可信的工具运行上下文。
        :return: 最多二十条长期记忆的紧凑执行结果。
        """
        raw_memories = await self.registry.execute_async(
            RECALL_USER_MEMORY_TOOL,
            runtime.user_id,
        )
        memories = [
            UserMemoryResponse.model_validate(memory)
            for memory in raw_memories
        ][:20]
        payload = {
            "ok": True,
            "count": len(memories),
            "memories": [
                {
                    "id": memory.id,
                    "type": memory.type,
                    "content": memory.content,
                }
                for memory in memories
            ],
        }
        return CoachToolExecution(
            tool_name=RECALL_USER_MEMORY_TOOL,
            content=_json_content(payload),
            observation=f"已按需读取 {len(memories)} 条长期记忆。",
            success=True,
        )

    async def _retrieve_knowledge(
        self,
        arguments: KnowledgeToolArguments,
    ) -> CoachToolExecution:
        """
        根据模型提供的问题检索本地健身知识。

        :param arguments: 已通过 Pydantic 校验的检索参数。
        :return: 健身知识条目和来源信息。
        """
        raw_items = await self.registry.execute_async(
            RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
            KnowledgeQuery(
                query=arguments.query,
                limit=arguments.limit,
            ),
        )
        items = tuple(
            FitnessKnowledgeItem.model_validate(item)
            for item in raw_items
        )
        payload = {
            "ok": True,
            "count": len(items),
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "category": item.category,
                    "content": item.content,
                    "summary": item.summary,
                }
                for item in items
            ],
        }
        return CoachToolExecution(
            tool_name=RETRIEVE_FITNESS_KNOWLEDGE_TOOL,
            content=_json_content(payload),
            observation=f"已按需检索 {len(items)} 条本地健身知识。",
            success=True,
            knowledge_items=items,
        )


def _error_execution(
    tool_name: str,
    error_code: str,
    *,
    observation: str,
    details: Any = None,
) -> CoachToolExecution:
    """
    构建不泄露内部实现的工具错误结果。

    :param tool_name: 被拒绝或执行失败的工具名称。
    :param error_code: 返回给模型的稳定错误代码。
    :param observation: 写入工作记忆的安全摘要。
    :param details: 可选的参数校验详情。
    :return: 标记为失败的工具执行结果。
    """
    payload: dict[str, Any] = {
        "ok": False,
        "error": error_code,
    }
    if details is not None:
        payload["details"] = details
    return CoachToolExecution(
        tool_name=tool_name,
        content=_json_content(payload),
        observation=observation,
        success=False,
    )


def _json_content(payload: dict[str, Any]) -> str:
    """
    将工具结果序列化为紧凑 JSON。

    :param payload: 待返回给大模型的结构化结果。
    :return: 保留中文并压缩空白的 JSON 文本。
    """
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
