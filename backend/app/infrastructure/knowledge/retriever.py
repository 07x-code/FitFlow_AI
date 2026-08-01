import json
from dataclasses import dataclass
from pathlib import Path

from app.domain.models import FitnessKnowledgeItem


DEFAULT_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "fitness_knowledge.json"
)


@dataclass(frozen=True)
class KnowledgeRetriever:
    items: tuple[FitnessKnowledgeItem, ...]

    @classmethod
    def from_default_file(cls) -> "KnowledgeRetriever":
        return cls.from_json_file(DEFAULT_KNOWLEDGE_PATH)

    @classmethod
    def from_json_file(cls, path: Path) -> "KnowledgeRetriever":
        raw_items = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            raise ValueError("Knowledge base root must be a JSON array.")

        return cls(
            items=tuple(
                FitnessKnowledgeItem.model_validate(raw_item)
                for raw_item in raw_items
            )
        )

    def retrieve(
        self,
        query: str,
        *,
        limit: int = 3,
    ) -> list[FitnessKnowledgeItem]:
        if limit <= 0:
            return []

        normalized_query = query.casefold()  #casefold忽略大小写
        scored_items: list[tuple[int, int, FitnessKnowledgeItem]] = []  
        #[int, int, FitnessKnowledgeItem] =(相关分数, 原始位置, 知识对象)

        for index, item in enumerate(self.items):
            #enumerate() 同时获得位置和元素 index位置，item元素
            score = _score_item(normalized_query, item)
            if score > 0:
                scored_items.append((score, index, item))

        scored_items.sort(key=lambda result: (-result[0], result[1]))
        #result[0]：分数，result[1]：原始位置 ，-result[0] 让分数从高到低排列
        return [item for _, _, item in scored_items[:limit]]


def _score_item(query: str, item: FitnessKnowledgeItem) -> int:
    score = 0

    if item.title.casefold() in query:
        score += 10

    for keyword in item.keywords:
        if keyword.casefold() in query:
            score += 6

    if item.category.casefold() in query:
        score += 3

    if any(
        keyword.casefold() in item.content.casefold()
        and keyword.casefold() in query
        for keyword in item.keywords
    ):
        score += 1

    return score