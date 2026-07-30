from typing import Protocol

from app.domain.models import FitnessKnowledgeItem


class KnowledgeRetrieverPort(Protocol):
    """健身知识检索端口。"""

    def retrieve(
        self,
        query: str,
        *,
        limit: int = 3,
    ) -> list[FitnessKnowledgeItem]:
        """
        检索与问题相关的健身知识。

        :param query: 用户问题。
        :param limit: 最大返回条目数。
        :return: 相关健身知识列表。
        """
