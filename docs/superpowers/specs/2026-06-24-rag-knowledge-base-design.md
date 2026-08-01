# FitFlow AI RAG 健身知识库 v1 设计

## 1. 目标

为 AI Coach Chat 增加一个可控、可测试、离线可运行的小型健身知识库，使回答能够引用明确的健身知识来源。

第一版重点不是构建复杂的向量数据库，而是验证完整 RAG 流程：

```text
用户问题
-> 风险规则检查
-> 本地知识检索
-> 组装用户上下文和知识上下文
-> 调用 LLM
-> 返回回答和知识来源
```

## 2. 范围

本次实现包括：

- JSON 格式的本地健身知识库。
- 基于关键词的确定性检索。
- 最多返回 3 条相关知识。
- 将检索结果加入 Coach Chat 提示词。
- 在 Coach Chat 响应中返回知识来源。
- 保持现有风险规则优先级。
- 使用 Fake Provider 完成离线自动化测试。

本次不包括：

- 向量数据库。
- Embedding 模型。
- 联网搜索。
- 管理后台或知识编辑接口。
- 自动从用户对话写入知识库。

## 3. 方案选择

采用“JSON 知识库 + 关键词评分”。

相比 Markdown 文档解析，这种方式的数据结构更稳定，测试更直接。相比向量数据库，它不需要额外服务、模型和网络调用，更适合当前项目阶段。知识检索通过独立接口封装，后续可以替换为向量检索，而不需要重写 Coach Chat。

## 4. 模块设计

### 4.1 知识数据

新增：

```text
app/data/fitness_knowledge.json
```

每条知识的数据结构：

```json
{
  "id": "rpe-basics",
  "title": "RPE 基础说明",
  "category": "训练强度",
  "keywords": ["RPE", "强度", "力竭", "太累"],
  "content": "RPE 7 表示完成当前组后大约还能再做 3 次重复。",
  "summary": "使用 RPE 衡量训练强度，初学者通常无需频繁练到力竭。"
}
```

首批知识覆盖：

- 新手训练原则。
- RPE 与训练强度。
- 热身与恢复。
- 常见动作替代。
- 疼痛与安全提醒。

### 4.2 领域模型

新增内部知识模型和 API 来源模型：

```text
FitnessKnowledgeItem
KnowledgeSource
```

`KnowledgeSource` 对外包含：

```text
title
category
summary
```

`CoachChatResponse` 新增：

```text
knowledge_sources: list[KnowledgeSource]
```

默认值为空列表，保证没有命中知识或被安全规则拦截时响应结构稳定。

### 4.3 检索服务

新增：

```text
app/services/knowledge_retriever.py
```

职责：

- 启动时或首次使用时读取 JSON。
- 校验知识数据结构。
- 根据用户问题计算相关度。
- 返回最多 3 条知识。

评分规则：

- 标题命中权重最高。
- `keywords` 命中权重次高。
- 分类和正文命中提供补充分数。
- 英文匹配忽略大小写。
- 没有有效命中时返回空列表。
- 分数相同时按照 JSON 中的稳定顺序返回。

检索服务只负责“找资料”，不负责调用 LLM，也不读取用户画像。

### 4.4 Coach Chat 集成

`CoachChatService` 新增 `knowledge_retriever` 依赖。

正常流程：

1. 查找用户画像。
2. 执行现有风险评估。
3. 若风险不允许自动建议，直接返回安全提醒。
4. 读取最近训练计划和长期记忆。
5. 使用用户问题检索知识。
6. 将知识标题、分类和正文加入 Prompt。
7. 调用当前配置的 LLM Provider。
8. 返回回答、计划 ID、安全等级和知识来源。

高风险流程不会调用检索服务和 LLM，返回：

```json
{
  "knowledge_sources": []
}
```

## 5. API 契约

接口保持不变：

```text
POST /api/coach/chat
```

响应示例：

```json
{
  "answer": "RPE 7 表示这一组结束后大约还能完成 3 次重复。",
  "safety_level": "low",
  "referenced_plan_id": 12,
  "knowledge_sources": [
    {
      "title": "RPE 基础说明",
      "category": "训练强度",
      "summary": "使用 RPE 衡量训练强度，初学者通常无需频繁练到力竭。"
    }
  ]
}
```

## 6. 错误处理

- JSON 文件不存在或格式无效时，应用应明确报错，避免悄悄使用空知识库。
- 单条知识缺少必要字段时，由模型校验给出错误。
- 没有检索结果不视为错误，Coach Chat 可以继续使用画像、计划和长期记忆回答。
- LLM Provider 的异常继续沿用现有处理方式，本次不改变其网络错误策略。

## 7. 测试设计

新增知识检索服务测试：

- “RPE 是什么”命中 `RPE 基础说明`。
- “深蹲太难怎么替代”命中动作替代知识。
- 无关问题返回空列表。
- 返回数量不超过 3 条。
- 相同输入获得稳定结果。

扩展 Coach Chat API 测试：

- Prompt 包含命中的知识正文。
- 响应包含 `title`、`category`、`summary`。
- 没有命中时 `knowledge_sources` 为空列表。
- 高风险画像直接拦截，并返回空知识来源。
- 原有最近训练计划、长期记忆和 Fake Provider 行为保持正常。

完成前运行：

```powershell
python -m pytest tests\test_knowledge_retriever.py -v
python -m pytest tests\test_coach_chat_api.py tests\test_memories_api.py -v
python -m pytest -v
```

## 8. 完成标准

- Coach Chat 能根据问题检索本地健身知识。
- 命中的知识正文会进入 LLM Prompt。
- API 返回可展示的知识来源。
- 无匹配时不伪造来源。
- 高风险输入继续优先走确定性安全规则。
- 默认测试不联网、不消耗 DashScope Token。
- 全量测试通过。

## 9. 后续升级路径

后续可以保留相同的检索接口，将实现替换为：

```text
JSON 关键词检索
-> Embedding 向量检索
-> metadata 过滤
-> 混合检索与重排序
-> 检索质量评估
```

第一版不会提前引入这些复杂度。
