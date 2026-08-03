from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.tools.coach import (
    CoachReadOnlyToolExecutor,
    CoachToolExecution,
    CoachToolRuntime,
)
from app.domain.models import FitnessKnowledgeItem
from app.ports.llm import LLMMessage, LLMProvider, LLMToolCall


class CoachToolAgentState(TypedDict, total=False):
    """Coach 受控工具调用图的共享状态。"""

    messages: list[LLMMessage]
    user_id: str
    session_id: str
    tool_iterations: int
    pending_tool_calls: tuple[LLMToolCall, ...]
    final_answer: str
    referenced_plan_id: int | None
    knowledge_items: list[FitnessKnowledgeItem]
    tool_executions: list[CoachToolExecution]


class CoachToolGraphBuilder:
    """构建只允许白名单只读工具的 Coach LangGraph。"""

    def __init__(
        self,
        *,
        llm_provider: LLMProvider,
        tool_executor: CoachReadOnlyToolExecutor,
        max_tool_iterations: int = 5,
    ) -> None:
        """
        初始化 Coach 工具调用图构建器。

        :param llm_provider: 支持结构化工具调用的大模型端口。
        :param tool_executor: 注入可信运行时上下文的只读工具执行器。
        :param max_tool_iterations: 单次对话允许的最大工具调用轮数。
        :return: 无返回值。
        """
        if max_tool_iterations < 1:
            raise ValueError("max_tool_iterations must be at least 1.")
        self.llm_provider = llm_provider
        self.tool_executor = tool_executor
        self.max_tool_iterations = max_tool_iterations

    def build(self):
        """
        构建并编译 Coach 受控工具调用图。

        :return: 可执行的 LangGraph 实例。
        """
        workflow = StateGraph(CoachToolAgentState)
        workflow.add_node("call_model", self._call_model)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("force_final_answer", self._force_final_answer)

        workflow.add_edge(START, "call_model")
        workflow.add_conditional_edges(
            "call_model",
            self._route_after_model,
            {
                "execute_tools": "execute_tools",
                "force_final_answer": "force_final_answer",
                "done": END,
            },
        )
        workflow.add_edge("execute_tools", "call_model")
        workflow.add_edge("force_final_answer", END)
        return workflow.compile()

    def _call_model(
        self,
        state: CoachToolAgentState,
    ) -> CoachToolAgentState:
        """
        让模型选择只读工具或生成最终回答。

        :param state: 当前 Coach 工具调用状态。
        :return: 包含模型消息、待执行工具或最终回答的状态更新。
        """
        completion = self.llm_provider.complete_with_tools(
            state["messages"],
            self.tool_executor.definitions(),
        )
        if completion.tool_calls:
            assistant_message = LLMMessage(
                role="assistant",
                content=completion.content,
                tool_calls=completion.tool_calls,
            )
            return {
                "messages": [*state["messages"], assistant_message],
                "pending_tool_calls": completion.tool_calls,
            }

        answer = (completion.content or "").strip()
        if not answer:
            answer = "当前无法生成有效回答，请稍后重试。"
        return {
            "final_answer": answer,
            "pending_tool_calls": (),
        }

    def _route_after_model(
        self,
        state: CoachToolAgentState,
    ) -> Literal["execute_tools", "force_final_answer", "done"]:
        """
        根据模型结果和调用上限选择下一节点。

        :param state: 已包含模型本轮结果的状态。
        :return: 执行工具、强制收尾或结束运行的路由名称。
        """
        if not state.get("pending_tool_calls"):
            return "done"
        if state.get("tool_iterations", 0) >= self.max_tool_iterations:
            return "force_final_answer"
        return "execute_tools"

    def _execute_tools(
        self,
        state: CoachToolAgentState,
    ) -> CoachToolAgentState:
        """
        顺序校验并执行模型本轮请求的白名单工具。

        :param state: 包含待执行工具调用的状态。
        :return: 包含工具消息、来源和观察记录的状态更新。
        """
        runtime = CoachToolRuntime(
            user_id=state["user_id"],
            session_id=state["session_id"],
        )
        messages = list(state["messages"])
        executions = list(state.get("tool_executions", []))
        knowledge_items = list(state.get("knowledge_items", []))
        referenced_plan_id = state.get("referenced_plan_id")

        for call in state.get("pending_tool_calls", ()):
            execution = self.tool_executor.execute(call, runtime)
            executions.append(execution)
            knowledge_items.extend(execution.knowledge_items)
            if execution.referenced_plan_id is not None:
                referenced_plan_id = execution.referenced_plan_id
            messages.append(
                LLMMessage(
                    role="tool",
                    content=execution.content,
                    tool_call_id=call.id,
                )
            )

        return {
            "messages": messages,
            "tool_iterations": state.get("tool_iterations", 0) + 1,
            "pending_tool_calls": (),
            "referenced_plan_id": referenced_plan_id,
            "knowledge_items": knowledge_items,
            "tool_executions": executions,
        }

    def _force_final_answer(
        self,
        state: CoachToolAgentState,
    ) -> CoachToolAgentState:
        """
        达到调用上限后关闭工具并要求模型直接收尾。

        :param state: 已达到工具调用上限的状态。
        :return: 不再包含待执行工具的最终回答状态。
        """
        messages = [
            *state["messages"],
            LLMMessage(
                role="system",
                content=(
                    "本次工具调用已达到上限。禁止继续调用工具，"
                    "请仅根据已有可靠信息回答；信息不足时明确说明。"
                ),
            ),
        ]
        completion = self.llm_provider.complete_with_tools(messages, ())
        answer = (completion.content or "").strip()
        if not answer:
            answer = (
                "本次工具调用已达到上限，现有信息不足以生成可靠回答。"
            )
        return {
            "messages": messages,
            "pending_tool_calls": (),
            "final_answer": answer,
        }


def create_coach_tool_graph(
    *,
    llm_provider: LLMProvider,
    tool_executor: CoachReadOnlyToolExecutor,
    max_tool_iterations: int = 5,
):
    """
    创建 AI Coach 使用的受控只读工具调用图。

    :param llm_provider: 支持结构化工具调用的大模型端口。
    :param tool_executor: Coach 只读工具执行器。
    :param max_tool_iterations: 单次对话最大工具调用轮数。
    :return: 已编译的 Coach LangGraph。
    """
    return CoachToolGraphBuilder(
        llm_provider=llm_provider,
        tool_executor=tool_executor,
        max_tool_iterations=max_tool_iterations,
    ).build()
