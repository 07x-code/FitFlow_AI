# FitFlow AI RAG Knowledge Base v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Coach Chat 增加本地 JSON 健身知识检索，并在回答中返回包含标题、分类和摘要的知识来源。

**Architecture:** 使用独立的 `KnowledgeRetriever` 读取并校验本地 JSON，通过确定性关键词评分返回 Top 3 知识。`CoachChatService` 在风险检查通过后执行检索，将知识正文加入 Prompt，并把精简来源加入 API 响应；高风险分支跳过检索和 LLM。

**Tech Stack:** Python 3.11、FastAPI、Pydantic、pytest、标准库 `json`/`pathlib`

---

## File Map

- Create: `app/data/fitness_knowledge.json`
  - 保存第一批结构化健身知识。
- Create: `app/services/knowledge_retriever.py`
  - 读取、校验、评分和排序知识。
- Create: `tests/test_knowledge_retriever.py`
  - 验证命中、无匹配、Top 3 和稳定排序。
- Modify: `app/domain/models.py`
  - 增加内部知识模型、来源模型和 Coach Chat 响应字段。
- Modify: `app/services/coach_chat.py`
  - 注入检索器、构建知识上下文并返回来源。
- Modify: `tests/test_coach_chat_api.py`
  - 验证 API 来源、Prompt 注入、无匹配和高风险行为。

### Task 1: 本地知识模型和确定性检索器

**Files:**
- Create: `tests/test_knowledge_retriever.py`
- Create: `app/data/fitness_knowledge.json`
- Create: `app/services/knowledge_retriever.py`
- Modify: `app/domain/models.py:142`

- [ ] **Step 1: 编写检索器失败测试**

创建 `tests/test_knowledge_retriever.py`：

```python
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

    first_results = retriever.retrieve("新手训练强度、热身、恢复和疼痛", limit=3)
    second_results = retriever.retrieve("新手训练强度、热身、恢复和疼痛", limit=3)

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
```

- [ ] **Step 2: 运行测试并确认因模块不存在而失败**

Run:

```powershell
python -m pytest tests\test_knowledge_retriever.py -v
```

Expected: collection error，包含：

```text
ModuleNotFoundError: No module named 'app.services.knowledge_retriever'
```

- [ ] **Step 3: 增加知识领域模型**

在 `app/domain/models.py` 的 `CoachChatRequest` 之前增加：

```python
class FitnessKnowledgeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    content: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class KnowledgeSource(BaseModel):
    title: str
    category: str
    summary: str
```

- [ ] **Step 4: 创建首批 JSON 知识**

创建 `app/data/fitness_knowledge.json`：

```json
[
  {
    "id": "beginner-training-principles",
    "title": "新手训练基本原则",
    "category": "新手训练",
    "keywords": ["新手", "入门", "训练频率", "每周几次", "循序渐进"],
    "content": "健身新手应优先学习稳定动作和规律训练。每周安排 2 到 4 次训练，并在动作质量稳定后逐步增加重量、次数或组数，通常比频繁更换计划更容易观察进步。",
    "summary": "新手应保持规律训练、重视动作质量，并采用循序渐进的训练方式。"
  },
  {
    "id": "rpe-basics",
    "title": "RPE 基础说明",
    "category": "训练强度",
    "keywords": ["RPE", "训练强度", "力竭", "太累", "还能做几次"],
    "content": "RPE 用于描述一组训练的主观用力程度。RPE 7 表示大约还能完成 3 次重复，RPE 8 表示大约还能完成 2 次。新手多数训练组可以保留一定余力，不需要每组都练到力竭。",
    "summary": "使用 RPE 衡量训练强度，初学者通常无需频繁练到力竭。"
  },
  {
    "id": "warmup-and-recovery",
    "title": "热身与训练恢复",
    "category": "恢复",
    "keywords": ["热身", "恢复", "休息", "睡眠", "肌肉酸痛", "腿酸"],
    "content": "训练前可先进行低强度活动和目标动作的轻重量练习。训练后应保证休息、睡眠和正常饮食。如果只是轻度延迟性肌肉酸痛，可以降低当天强度；如果疼痛尖锐、持续加重或影响正常活动，应停止相关训练并寻求专业帮助。",
    "summary": "热身应从低强度开始，恢复需要睡眠和休息，异常疼痛需要停止训练。"
  },
  {
    "id": "squat-substitution",
    "title": "深蹲动作替代",
    "category": "动作替代",
    "keywords": ["深蹲", "替代动作", "动作太难", "腿部训练", "器械限制"],
    "content": "如果徒手或杠铃深蹲暂时难以稳定完成，可以根据目标和器械条件选择高脚杯深蹲、坐姿腿举或箱式深蹲。替代动作仍应保持可控动作范围，并选择不会引起疼痛的方案。",
    "summary": "深蹲困难时可选择高脚杯深蹲、腿举或箱式深蹲作为替代。"
  },
  {
    "id": "pain-safety-guidance",
    "title": "疼痛与训练安全提醒",
    "category": "训练安全",
    "keywords": ["疼痛", "胸痛", "急性损伤", "受伤", "头晕", "不舒服"],
    "content": "训练中出现胸痛、明显呼吸困难、晕厥感、急性损伤或快速加重的疼痛时，不应继续训练，也不应依赖 AI 判断疾病，应及时寻求专业医疗帮助。",
    "summary": "胸痛、急性损伤或明显异常症状需要停止训练并寻求专业帮助。"
  }
]
```

- [ ] **Step 5: 实现最小检索器**

创建 `app/services/knowledge_retriever.py`：

```python
import json
from dataclasses import dataclass
from pathlib import Path

from app.domain.models import FitnessKnowledgeItem


DEFAULT_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "fitness_knowledge.json"
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

        normalized_query = query.casefold()
        scored_items: list[tuple[int, int, FitnessKnowledgeItem]] = []

        for index, item in enumerate(self.items):
            score = _score_item(normalized_query, item)
            if score > 0:
                scored_items.append((score, index, item))

        scored_items.sort(key=lambda result: (-result[0], result[1]))
        return [item for _, _, item in scored_items[:limit]]


def _score_item(query: str, item: FitnessKnowledgeItem) -> int:
    score = 0
    title = item.title.casefold()
    category = item.category.casefold()

    if title in query:
        score += 10

    for keyword in item.keywords:
        normalized_keyword = keyword.casefold()
        if normalized_keyword in query:
            score += 6

    if category in query:
        score += 3

    if any(
        keyword.casefold() in item.content.casefold()
        and keyword.casefold() in query
        for keyword in item.keywords
    ):
        score += 1

    return score
```

- [ ] **Step 6: 运行检索器测试并确认通过**

Run:

```powershell
python -m pytest tests\test_knowledge_retriever.py -v
```

Expected:

```text
5 passed
```

- [ ] **Step 7: 由用户提交第一阶段**

```powershell
git add app\data\fitness_knowledge.json app\services\knowledge_retriever.py app\domain\models.py tests\test_knowledge_retriever.py
git commit -m "feat: 添加本地健身知识检索"
```

### Task 2: 将知识检索接入 Coach Chat

**Files:**
- Modify: `app/domain/models.py:146`
- Modify: `app/services/coach_chat.py`
- Modify: `tests/test_coach_chat_api.py`

- [ ] **Step 1: 编写 API 来源和 Prompt 注入失败测试**

在 `tests/test_coach_chat_api.py` 末尾增加：

```python
def test_coach_chat_returns_rpe_knowledge_source_and_uses_content_in_prompt():
    client = TestClient(app)
    user_id = unique_user_id("coach-rag-rpe-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers={"X-User-ID": user_id},
        json={"message": "RPE 是什么？"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["knowledge_sources"] == [
        {
            "title": "RPE 基础说明",
            "category": "训练强度",
            "summary": "使用 RPE 衡量训练强度，初学者通常无需频繁练到力竭。",
        }
    ]
    assert "RPE 7 表示大约还能完成 3 次重复" in body["answer"]
```

- [ ] **Step 2: 运行新增测试并确认响应缺少字段**

Run:

```powershell
python -m pytest tests\test_coach_chat_api.py::test_coach_chat_returns_rpe_knowledge_source_and_uses_content_in_prompt -v
```

Expected: FAIL，包含：

```text
KeyError: 'knowledge_sources'
```

- [ ] **Step 3: 扩展 Coach Chat 响应模型**

修改 `app/domain/models.py`：

```python
class CoachChatResponse(BaseModel):
    answer: str
    safety_level: str
    referenced_plan_id: int | None = None
    knowledge_sources: list[KnowledgeSource] = Field(default_factory=list)
```

- [ ] **Step 4: 给 CoachChatService 注入检索器**

修改 `app/services/coach_chat.py` 的导入：

```python
from app.domain.models import (
    CoachChatRequest,
    CoachChatResponse,
    FitnessKnowledgeItem,
    FitnessProfileCreate,
    KnowledgeSource,
    TrainingPlanHistoryItem,
    UserMemoryResponse,
)
from app.services.knowledge_retriever import KnowledgeRetriever
```

给 `CoachChatService` 增加字段：

```python
knowledge_retriever: KnowledgeRetriever
```

修改工厂函数：

```python
def create_coach_chat_service(
    profile_repository: ProfileRepository,
    training_plan_repository: TrainingPlanRepository,
    llm_provider: LLMProvider | None = None,
    memory_repository: UserMemoryRepository | None = None,
    knowledge_retriever: KnowledgeRetriever | None = None,
) -> CoachChatService:
    return CoachChatService(
        profile_repository=profile_repository,
        training_plan_repository=training_plan_repository,
        memory_repository=memory_repository or UserMemoryRepository(),
        knowledge_retriever=(
            knowledge_retriever or KnowledgeRetriever.from_default_file()
        ),
        llm_provider=llm_provider or create_llm_provider(),
    )
```

- [ ] **Step 5: 在低风险流程中检索并返回来源**

在 `chat()` 中，读取长期记忆后增加：

```python
knowledge_items = self.knowledge_retriever.retrieve(request.message)
```

调用 `_build_coach_chat_prompt()` 时传入：

```python
knowledge_items=knowledge_items,
```

正常响应增加：

```python
knowledge_sources=[
    KnowledgeSource(
        title=item.title,
        category=item.category,
        summary=item.summary,
    )
    for item in knowledge_items
],
```

- [ ] **Step 6: 将知识正文加入 Prompt**

给 `_build_coach_chat_prompt()` 增加参数：

```python
knowledge_items: list[FitnessKnowledgeItem],
```

在返回 Prompt 之前构建：

```python
knowledge_context = "未检索到与当前问题直接相关的本地健身知识。"
if knowledge_items:
    knowledge_context = "\n".join(
        (
            f"- 标题：{item.title}\n"
            f"  分类：{item.category}\n"
            f"  内容：{item.content}"
        )
        for item in knowledge_items
    )
```

在 Prompt 末尾加入：

```python
f"\n健身知识库依据：\n{knowledge_context}"
```

- [ ] **Step 7: 运行新增 API 测试并确认通过**

Run:

```powershell
python -m pytest tests\test_coach_chat_api.py::test_coach_chat_returns_rpe_knowledge_source_and_uses_content_in_prompt -v
```

Expected:

```text
1 passed
```

- [ ] **Step 8: 运行 Coach Chat 和长期记忆回归测试**

Run:

```powershell
python -m pytest tests\test_coach_chat_api.py tests\test_memories_api.py -v
```

Expected: 原有测试中高风险精确响应断言暂时失败，因为新增了 `knowledge_sources` 字段；其他测试通过。

- [ ] **Step 9: 由用户提交第二阶段**

此时先不提交，等 Task 3 补齐高风险和无匹配契约后一起提交。

### Task 3: 补齐无匹配与高风险安全分支

**Files:**
- Modify: `app/services/coach_chat.py`
- Modify: `tests/test_coach_chat_api.py`

- [ ] **Step 1: 编写无匹配来源测试**

在 `tests/test_coach_chat_api.py` 末尾增加：

```python
def test_coach_chat_returns_no_sources_for_unrelated_question():
    client = TestClient(app)
    user_id = unique_user_id("coach-rag-unrelated-user")
    save_profile(client, user_id)

    response = client.post(
        "/api/coach/chat",
        headers={"X-User-ID": user_id},
        json={"message": "Python 的装饰器是什么？"},
    )

    assert response.status_code == 200
    assert response.json()["knowledge_sources"] == []
```

- [ ] **Step 2: 更新高风险响应契约测试**

在 `test_coach_chat_blocks_risky_profile_without_calling_llm` 的预期字典中增加：

```python
"knowledge_sources": [],
```

该测试保留原有精确字典断言，确保高风险分支不会返回任何知识来源。

- [ ] **Step 3: 运行两个安全契约测试**

Run:

```powershell
python -m pytest tests\test_coach_chat_api.py::test_coach_chat_returns_no_sources_for_unrelated_question tests\test_coach_chat_api.py::test_coach_chat_blocks_risky_profile_without_calling_llm -v
```

Expected:

```text
2 passed
```

如果高风险测试失败，在 `CoachChatService.chat()` 的 blocked 响应中显式增加：

```python
knowledge_sources=[],
```

- [ ] **Step 4: 运行 RAG 与 Coach Chat 相关测试**

Run:

```powershell
python -m pytest tests\test_knowledge_retriever.py tests\test_coach_chat_api.py tests\test_memories_api.py -v
```

Expected: 全部通过，仅允许现有 `StarletteDeprecationWarning`。

- [ ] **Step 5: 运行全量测试**

Run:

```powershell
python -m pytest -v
```

Expected: 全部测试通过，无失败。

- [ ] **Step 6: 检查改动范围和空白错误**

Run:

```powershell
git diff --check
git status --short
```

Expected:

- `git diff --check` 退出码为 0。
- 仅出现本计划列出的代码、测试和数据文件。
- Windows 下可能显示 LF 转 CRLF 提示，但不能有 trailing whitespace 错误。

- [ ] **Step 7: 由用户提交完整 RAG v1**

```powershell
git add app\data\fitness_knowledge.json app\domain\models.py app\services\knowledge_retriever.py app\services\coach_chat.py tests\test_knowledge_retriever.py tests\test_coach_chat_api.py
git commit -m "feat: 添加 RAG 健身知识库"
git push origin main
```

## Final Verification Checklist

- [ ] `RPE 是什么` 命中 RPE 知识。
- [ ] `深蹲太难怎么替代` 命中动作替代知识。
- [ ] 无关问题返回空来源。
- [ ] 最多返回 3 条且排序稳定。
- [ ] Prompt 包含完整知识正文。
- [ ] API 来源只暴露标题、分类和摘要。
- [ ] 高风险画像跳过知识来源并保持安全拦截。
- [ ] Fake Provider 测试不联网、不消耗 Token。
- [ ] 全量 pytest 通过。
