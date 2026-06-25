import pytest

from app.services.knowledge_retriever import KnowledgeRetriever


def test_retrieve_matches_rpe_knowledge():
    retriever = KnowledgeRetriever.from_default_file()

    results = retriever.retrieve("RPE 是什么？")

    assert results[0].id == "rpe-basics"
    assert results[0].title == "RPE 基础说明"


def test_retrieve_matches_exercise_substitution():
    retriever = KnowledgeRetriever.from_default_file()

    results = retriever.retrieve("深蹲太难了，可以用什么动作替代？")

    assert results[0].id == "squat-substitution"


def test_retrieve_returns_empty_for_unrelated_question():
    retriever = KnowledgeRetriever.from_default_file()

    results = retriever.retrieve("Python 的装饰器是什么？")

    assert results == []


def test_retrieve_limits_results_to_three_and_is_stable():
    retriever = KnowledgeRetriever.from_default_file()

    first_results = retriever.retrieve(
        "新手训练强度、热身、恢复和疼痛",
        limit=3,
    )
    second_results = retriever.retrieve(
        "新手训练强度、热身、恢复和疼痛",
        limit=3,
    )

    assert len(first_results) == 3
    assert [item.id for item in first_results] == [
        item.id for item in second_results
    ]


def test_from_json_file_rejects_non_array_root(tmp_path):
    knowledge_path = tmp_path / "invalid-knowledge.json"
    knowledge_path.write_text("{}", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Knowledge base root must be a JSON array.",
    ):
        KnowledgeRetriever.from_json_file(knowledge_path)
