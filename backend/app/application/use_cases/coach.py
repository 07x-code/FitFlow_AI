from dataclasses import dataclass

from app.application.errors import NotFoundError
from app.domain.models import CoachChatRequest, CoachChatResponse
from app.ports.ai import CoachAgentPort


@dataclass(frozen=True)
class CoachUseCases:
    """AI 教练应用用例。"""

    agent: CoachAgentPort

    def chat(
        self,
        user_id: str,
        request: CoachChatRequest,
    ) -> CoachChatResponse:
        """
        处理用户的 AI 教练对话。

        :param user_id: 用户标识。
        :param request: 教练对话请求。
        :return: AI 教练回复。
        """
        response = self.agent.chat(user_id, request)
        if response is None:
            raise NotFoundError("Profile not found.")
        return response
