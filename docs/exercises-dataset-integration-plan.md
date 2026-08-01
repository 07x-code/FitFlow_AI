# FitFlow AI 动作数据集集成专项计划

> 配套总路线图：`docs/fitflow-helloagents-autumn-recruitment-roadmap.md`  
> 本地数据集：`F:\python_project\exercises-dataset`  
> 上游仓库：`https://github.com/hasaneyldrm/exercises-dataset`  
> 文档日期：2026-07-28

## 1. 数据集概况

本地数据集统计：

| 项目 | 数量或大小 |
|---|---:|
| 动作记录 | 1,324 |
| JSON 数据 | 约 17 MB |
| 图片 | 1,324 张，约 8.46 MB |
| GIF | 1,324 个，约 122.78 MB |
| 身体部位 | 10 类 |
| 器械 | 28 类 |
| 目标肌肉 | 19 类 |
| 动作说明语言 | 10 种 |

主要字段：

- `id`
- `name`
- `category`
- `body_part`
- `equipment`
- `instructions`
- `instruction_steps`
- `muscle_group`
- `secondary_muscles`
- `target`
- `image`
- `gif_url`
- `attribution`
- `created_at`

## 2. 在 FitFlow 中的定位

该数据集应当成为 FitFlow 的“动作目录与动作知识数据源”，而不是直接替代安全规则，也不应将全部 JSON 注入大模型 Prompt。

建议处理链：

```text
上游 exercises.json
        ↓
Schema 校验与版本记录
        ↓
字段标准化与 FitFlow 安全增强
        ↓
SQLite 结构化动作目录
        ↓
关键词/向量检索索引
        ↓
ExerciseCatalogTool
        ↓
PlannerAgent 候选动作筛选
        ↓
确定性 Safety Guard
        ↓
训练计划
```

数据集适合提供：

- 动作 ID、名称和多语言说明。
- 身体部位、目标肌肉和辅助肌肉。
- 器械需求。
- 动作图片/GIF 路径与版权归属。
- 动作搜索、过滤和训练计划候选池。

FitFlow 仍需自行补充：

- 难度等级。
- 动作模式：推、拉、蹲、髋铰链、单腿、核心、负重行走等。
- 初学者适用性。
- 禁忌或慎用标签。
- 可替代动作关系。
- 单侧/双侧属性。
- 复合/孤立动作属性。
- 默认组数、次数、RPE 和休息建议。
- 对特定疼痛或健康风险的排除规则。

## 3. 版权和仓库策略

上游数据、结构和说明文字采用 MIT License；图片和 GIF 属于 Gym visual，适用独立媒体条款。

需要遵守：

- 媒体必须保留 `© Gym visual — https://gymvisual.com/` 归属。
- 媒体限制为 180×180 分辨率。
- 克隆上游仓库本身不等于获得新的媒体复用许可。
- 在自己的公开项目中复用前，应审阅 Gym visual 条款，并在需要时取得许可。

秋招项目建议采用以下策略：

1. FitFlow 主仓库只导入非媒体 JSON 字段和数据来源声明。
2. 不直接提交上游 `images/` 和 `videos/`。
3. Demo 默认展示动作文本、肌群和器械信息。
4. 如果展示媒体，必须保留每条记录的 attribution，并先确认许可范围。
5. 在 `THIRD_PARTY_NOTICES.md` 中记录来源、Commit SHA、许可证和导入日期。
6. 通过导入脚本从本地或固定上游版本构建数据，不手工复制和修改源文件。

## 4. 目标目录

```text
backend/
├── app/
│   ├── domain/
│   │   └── models/
│   │       └── exercise.py
│   ├── application/
│   │   └── use_cases/
│   │       ├── search_exercises.py
│   │       └── get_exercise_detail.py
│   ├── ai/
│   │   ├── tools/
│   │   │   └── knowledge/
│   │   │       └── exercise_catalog.py
│   │   └── knowledge/
│   │       ├── ingestion/
│   │       │   └── exercise_dataset.py
│   │       └── retrievers/
│   │           └── exercise_retriever.py
│   ├── ports/
│   │   └── exercise_catalog.py
│   └── infrastructure/
│       └── persistence/
│           └── sqlite/
│               └── exercise_repository.py
├── scripts/
│   ├── import_exercises.py
│   └── validate_exercises.py
└── tests/
    ├── fixtures/
    │   └── exercises.sample.json
    └── exercise_catalog/
```

主仓库只保留小型测试 Fixture，不复制完整媒体资源。

## 5. FitFlow 动作领域模型

建议将上游记录映射为：

```text
Exercise
├── id
├── source
├── source_version
├── name
├── localized_names
├── instructions
├── instruction_steps
├── body_part
├── target_muscle
├── secondary_muscles
├── equipment
├── movement_pattern
├── difficulty
├── beginner_friendly
├── unilateral
├── compound
├── contraindication_tags
├── substitution_ids
├── image_path
├── animation_path
└── attribution
```

上游原始字段与 FitFlow 增强字段必须分开：

- 原始字段可重新导入和追踪。
- 增强字段由 FitFlow 规则或人工审核维护。
- 不允许 LLM 直接写入安全相关增强字段。

## 6. 功能计划表

| 编号 | 功能 | 工作内容 | 验收标准 | 优先级 | 工作量 |
|---|---|---|---|---|---:|
| DATA-01 | 来源固定 | 记录上游 URL、Commit SHA、导入时间和许可证 | 每次导入结果可复现 | P0 | 0.5 天 |
| DATA-02 | Schema 校验 | 使用上游 JSON Schema 校验 1,324 条记录 | 记录数、ID 唯一性、必填字段全部通过 | P0 | 1 天 |
| DATA-03 | Pydantic 模型 | 建立 RawExercise 与 Exercise 模型 | 非法记录给出具体字段错误 | P0 | 1 天 |
| DATA-04 | 标准化 | 统一名称、器械、肌群和中文说明 | 生成标准化报告和异常清单 | P0 | 1-2 天 |
| DATA-05 | SQLite 导入 | 建立 exercise、muscle、equipment 和关联表 | 导入幂等，可按版本重建 | P0 | 2 天 |
| DATA-06 | Catalog API | 动作列表、详情、搜索和筛选 API | 支持分页、肌群、器械和身体部位筛选 | P0 | 2 天 |
| DATA-07 | Catalog Tool | `ExerciseCatalogTool` | Agent 只能通过类型化参数查询动作 | P0 | 1-2 天 |
| DATA-08 | 计划接入 | PlannerAgent 从候选动作池生成计划 | 正式计划中的动作 ID 必须存在于目录 | P0 | 2-3 天 |
| DATA-09 | 安全增强 | 难度、动作模式、初学者和禁忌标签 | 安全字段经过人工审核或规则测试 | P0 | 3-5 天 |
| DATA-10 | 替代关系 | 按器械、模式和肌群建立替代动作 | 无器械时可返回合理替代方案 | P1 | 2-3 天 |
| DATA-11 | RAG 索引 | 对名称、肌群和说明建立混合索引 | 动作查询 Recall@5 达到目标 | P1 | 2-3 天 |
| DATA-12 | 中文检索 | 支持中文肌群、器械和动作意图 | 中文标注查询集可复现评估 | P1 | 2 天 |
| DATA-13 | 前端浏览 | 动作搜索、筛选和详情页面 | 可从计划跳转动作说明 | P1 | 2-3 天 |
| DATA-14 | 媒体展示 | 可选展示图片/GIF 与 Attribution | 版权归属始终可见，资源缺失可降级 | P2 | 1-2 天 |
| DATA-15 | 数据同步 | 上游版本差异和增量导入 | 输出新增、修改、删除记录报告 | P2 | 2 天 |

## 7. API 规划

```text
GET /api/exercises
GET /api/exercises/{exercise_id}
GET /api/exercises/search
GET /api/exercises/filters
GET /api/exercises/{exercise_id}/substitutions
```

搜索参数：

```text
query
body_part
target
equipment
movement_pattern
difficulty
beginner_friendly
limit
offset
```

## 8. Agent 和 RAG 的边界

PlannerAgent 不应自由生成动作名称，而应：

1. 根据画像和计划目标构建结构化动作查询。
2. 调用 `ExerciseCatalogTool` 获得候选动作。
3. 使用确定性规则过滤禁忌和不适合初学者的动作。
4. 在安全候选池中选择动作并生成训练参数。
5. 保存上游 Exercise ID，而不是只保存动作文本。

CoachAgent 可以：

- 查询动作中文步骤。
- 解释目标肌肉和辅助肌肉。
- 根据用户器械条件查询替代动作。
- 返回数据来源和 attribution。

CoachAgent 不可以：

- 根据数据集内容诊断疼痛。
- 自动判定受伤后的康复动作。
- 绕过 Safety Guard 推荐被排除的动作。
- 将 GIF 动画视为专业动作纠正或医疗指导。

## 9. 数据集专项评估指标

| 指标 | 目标 |
|---|---:|
| 导入记录数 | 1,324 |
| 上游 ID 唯一率 | 100% |
| Schema 校验通过率 | 100% 或有明确异常清单 |
| 计划动作可追溯率 | 100% |
| 不存在动作进入正式计划 | 0 |
| 禁忌标签过滤通过率 | 100% |
| 中文动作查询 Recall@5 | ≥ 85% |
| 器械过滤准确率 | 100% |
| 替代动作规则测试通过率 | 100% |
| 媒体 Attribution 展示覆盖率 | 100% |

## 10. 与八周主计划的衔接

- W1：完成 DATA-01 至 DATA-05，建立可复现导入流程。
- W2：在 Memory 开发同时完成 Catalog API 和 Catalog Tool。
- W4：将动作说明纳入 RAG，建立中文动作查询评估集。
- W5：PlannerAgent 必须通过 ExerciseCatalogTool 获取候选动作。
- W7：根据许可确认情况决定是否展示媒体。

数据集集成后，秋招 Demo 增加：

1. 根据目标肌群和器械检索动作。
2. 生成计划时展示可追溯 Exercise ID。
3. 无指定器械时自动寻找替代动作。
4. 中文查询动作步骤和目标肌肉。
5. 展示安全过滤前后的候选动作差异。
6. 展示数据版本、来源和评估指标。

