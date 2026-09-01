from dataclasses import dataclass

from app.application.errors import NotFoundError
from app.domain.models import CoachChatRequest, CoachChatResponse
from app.ports.ai import CoachAgentPort

from app.application.use_cases.memories import MemoryUseCases


@dataclass(frozen=True)
class CoachUseCases:
    """AI 教练应用用例。"""

    agent: CoachAgentPort
    memories: MemoryUseCases | None = None

    async def chat(
        self,
        user_id: str,
        session_id: str,
        request: CoachChatRequest,
    ) -> CoachChatResponse:
        """
        处理用户的 AI 教练对话。

        :param user_id: 用户标识。
        :param session_id: 会话标识。
        :param request: 教练对话请求。
        :return: AI 教练回复。
        """
        memory_events = []
        if self.memories is not None:
            memory_events = await self.memories.capture_explicit(
                user_id,
                request.message,
            )

        response = await self.agent.chat(user_id, session_id, request)
        if response is None:
            raise NotFoundError("Profile not found.")
        if self.memories is None:
            return response
        return response.model_copy(
            update={"memory_events": memory_events}
        )
