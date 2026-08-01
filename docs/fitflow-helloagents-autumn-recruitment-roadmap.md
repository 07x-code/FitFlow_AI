# FitFlow AI 对标 HelloAgents 的秋招功能完善计划

> 文档日期：2026-07-28  
> 目标：将 FitFlow AI 完善为可用于 2026 年秋招展示、简历描述和技术面试的 Agent 项目。  
> 项目定位：安全约束下，具备记忆、RAG、工具调用、人工确认和可评估能力的多 Agent 健身教练。

## 1. 项目目标

FitFlow AI 不追求机械复刻 HelloAgents 的所有模块，而是选择与健身场景强相关、面试展示价值高的能力，形成一条清晰的技术主线：

```text
用户画像与训练记录
        ↓
确定性安全规则
        ↓
上下文构建 + 记忆召回 + RAG
        ↓
多 Agent 任务分派与工具调用
        ↓
计划或调整建议
        ↓
人工确认
        ↓
执行、反馈、评估与持续优化
```

最终需要证明的不是“调用过大模型”，而是：

1. 能设计清晰的 Agent 系统分层。
2. 能控制 LLM 的不确定性和安全边界。
3. 能实现记忆、RAG、工具调用和多 Agent 协作。
4. 能建立可量化的评估体系。
5. 能把 Agent 做成可运行、可测试、可部署的完整应用。

## 2. FitFlow 当前基础

### 2.1 已实现能力

- FastAPI 与 React PWA 前后端分离。
- Pydantic 领域模型与 SQLite 持久化。
- 用户画像、训练计划、训练记录、提案、周报和 AI Coach API。
- 基于规则的风险评估、训练计划生成和安全校验。
- LangGraph 训练计划工作流。
- `Agent`、`AgentMessage`、`Tool`、`ToolRegistry` 等基础抽象。
- `CoachAgent` 和 `TrainingPlanAgent`。
- Profile、Risk、Training Plan、Memory、Knowledge Retrieval 工具。
- 简单的长期用户记忆 Repository。
- 基于本地 JSON 和关键词匹配的轻量 RAG。
- DashScope/Qwen 与离线 Fake Provider。
- Proposal + 用户确认机制。
- 前后端与 Agent 层自动化测试，目前共 100 个测试。

### 2.2 当前关键判断

FitFlow 已经“拥有多个 Agent”，但还不是完整的“多 Agent 协作系统”：

- `CoachAgent` 与 `TrainingPlanAgent` 目前分别服务不同入口。
- 没有统一的任务协议、Supervisor、Agent Registry 和共享上下文。
- Agent 之间没有显式委派、结果汇总和失败回退。

FitFlow 已经“保存记忆”，但还没有形成完整的“记忆系统”：

- 目前主要是用户主动保存的长期文本记忆。
- 没有 Working、Episodic、Semantic 等分类。
- 没有 TTL、重要性、时间衰减、记忆固化、冲突合并和遗忘策略。

FitFlow 已经“有 RAG”，但还没有形成可展示的“高级 RAG”：

- 当前是本地 JSON + 关键词匹配。
- 没有文档导入、分块、Embedding、向量存储、混合检索、重排和引用评估。

## 3. HelloAgents 模块对比

成熟度定义：

- `0`：未实现。
- `1`：已有原型或局部能力。
- `2`：可以稳定使用，但展示深度不足。
- `3`：具备测试、指标、文档和完整 Demo，可用于秋招重点展示。

| HelloAgents 模块 | HelloAgents 代表能力 | FitFlow 当前状态 | 当前成熟度 | 秋招目标 | 优先级 |
|---|---|---|---:|---:|---|
| Core Framework | Agent、Message、Config、Exception | 已有 Agent、Message、Config，缺统一异常和运行结果 | 2 | 3 | P0 |
| LLM Layer | 多 Provider、本地模型、自动检测、流式输出 | DashScope 可真实调用，OpenAI 仍为 Dry Run | 2 | 3 | P1 |
| Agent Paradigms | Simple、ReAct、Reflection、Plan-and-Solve、Function Call | 有 CoachAgent 和 LangGraph Plan Agent | 1 | 2 | P1 |
| Tool System | Tool、Registry、参数描述、工具链、异步执行 | 已有类型化 Tool 和 Registry | 2 | 3 | P0 |
| Memory | Working、Episodic、Semantic、Perceptual、MemoryManager | 只有简单长期文本记忆 | 1 | 3 | P0 |
| RAG | 文档解析、分块、Embedding、向量库、高级检索 | JSON + 关键词匹配 | 1 | 3 | P0 |
| Context Engineering | ContextBuilder、GSSC、Token Budget、结构化笔记 | 当前手工拼接 Prompt | 1 | 3 | P0 |
| Multi-Agent | 角色划分、顺序/并行协作、结果汇总 | 多个独立 Agent，无协作协议 | 1 | 3 | P0 |
| MCP | 标准化外部工具接入、自定义 MCP Server | 未实现 | 0 | 2 | P1 |
| A2A / ANP | Agent 间通信、服务发现 | 未实现 | 0 | 0-1 | P2 |
| Evaluation | BFCL、GAIA、LLM Judge、Win Rate、报告 | 只有 pytest 功能测试 | 1 | 3 | P0 |
| Context Tools | NoteTool、TerminalTool、长任务上下文 | 无结构化 Agent 笔记 | 0 | 1-2 | P1 |
| Observability | 工具监听、任务进度、调用事件 | 未实现统一 Trace | 0 | 3 | P0 |
| Full-stack Case | 前后端分离、类型模型、进度、导出 | 已前后端分离，缺流式进度和结果导出 | 2 | 3 | P1 |
| Agentic RL | SFT、LoRA、GRPO、奖励函数 | 未实现 | 0 | 0 | P2 |

## 4. 秋招前的范围控制

### 4.1 必须完成

- 清晰的 AI 分层架构。
- Working、Episodic、Semantic 三类记忆。
- ContextBuilder 与 Token Budget。
- 可替换的向量检索或轻量混合检索。
- Supervisor + 3 至 4 个专家 Agent。
- 人工确认与确定性 Safety Guard。
- Agent Trace、工具调用日志和评估报告。
- Docker、CI、README、架构图和演示材料。

### 4.2 有时间再完成

- MCP 健身动作或运动数据工具。
- 流式输出和实时 Agent 进度。
- Function Calling。
- Reflection Agent。
- 异步或并行工具执行。
- PDF/Markdown 健身资料导入。

### 4.3 秋招前不建议投入

- Agentic RL、SFT、GRPO。
- Neo4j 知识图谱。
- ANP 服务发现。
- 复杂 A2A 分布式部署。
- 多模态动作识别。
- 微服务拆分。

这些模块成本高、验证困难，会削弱项目主线。可以在文档中作为未来方向，而不是秋招前的交付目标。

## 5. 目标代码架构

```text
backend/app/
├── api/                            # HTTP 接口层
│   ├── routes/
│   ├── schemas/
│   └── dependencies.py
├── application/                    # 应用用例层
│   ├── use_cases/
│   └── dto/
├── ai/                             # AI 能力层
│   ├── core/
│   │   ├── agent.py
│   │   ├── message.py
│   │   ├── task.py
│   │   ├── result.py
│   │   └── exceptions.py
│   ├── agents/
│   │   ├── single/
│   │   │   ├── coach.py
│   │   │   ├── planner.py
│   │   │   ├── reporter.py
│   │   │   └── adjustment.py
│   │   └── teams/
│   │       ├── supervisor.py
│   │       └── fitness_team.py
│   ├── orchestration/
│   │   ├── graphs/
│   │   ├── nodes/
│   │   └── protocols.py
│   ├── tools/
│   │   ├── profile/
│   │   ├── training/
│   │   ├── memory/
│   │   └── knowledge/
│   ├── memory/
│   │   ├── working.py
│   │   ├── episodic.py
│   │   ├── semantic.py
│   │   ├── manager.py
│   │   └── policies.py
│   ├── context/
│   │   ├── builder.py
│   │   ├── budget.py
│   │   └── session.py
│   ├── knowledge/
│   │   ├── ingestion/
│   │   ├── retrievers/
│   │   └── stores/
│   ├── prompts/
│   └── evaluation/
├── domain/                         # 纯业务和安全规则
│   ├── models/
│   ├── rules/
│   ├── services/
│   └── events/
├── ports/                          # LLM、Repository、VectorStore 抽象
├── infrastructure/                 # DashScope、SQLite、向量库等实现
│   ├── llm/
│   ├── persistence/
│   ├── vectorstore/
│   └── observability/
├── bootstrap/                      # 依赖注入与应用装配
└── main.py
```

### 5.1 强制依赖规则

- `domain` 不导入 FastAPI、Agent、SQLite 或 DashScope。
- `api` 只调用 `application` 用例。
- `ai` 依赖 `domain` 和 `ports`，不直接依赖具体数据库。
- `infrastructure` 实现 `ports`。
- Agent 不得直接修改安全结论。
- Safety Guard 必须是确定性组件，不使用自由生成的 LLM 判断。
- 所有用户数据和记忆必须通过 `user_id` 隔离。

## 6. 功能待完善计划表

### 6.1 P0：秋招核心能力

| 编号 | 模块 | 待实现内容 | 验收标准 | 预计工作量 |
|---|---|---|---|---:|
| ARC-01 | 架构 | 建立 `application/ai/ports/bootstrap` | API 不再直接实例化 Repository；依赖方向测试通过 | 2-3 天 |
| ARC-02 | Domain | 拆分超大的 `domain/models.py` | Profile、Plan、Workout、Memory、Report 模型独立 | 1-2 天（✅ 已完成：2026-07-30） |
| ARC-03 | DI | 建立 Container 和 Factory | Fake/真实 LLM、临时 DB 可通过依赖注入替换 | 1-2 天 |
| MEM-01 | Working Memory | 会话内消息、工具 Observation、TTL、容量限制 | 会话结束自动清理；不同用户不共享 | 2 天（✅ 已完成：2026-07-31） |
| MEM-02 | Episodic Memory | 保存对话、训练、疼痛和调整事件 | 支持按用户、时间、事件类型检索 | 2-3 天 |
| MEM-03 | Semantic Memory | 保存稳定偏好、器械和长期限制 | 支持更新、合并、删除和来源追踪 | 2-3 天 |
| MEM-04 | MemoryManager | 统一 add/search/update/delete/consolidate | Agent 只调用统一接口，不直接操作 Repository | 2 天 |
| MEM-05 | Memory Policy | 重要性、时间衰减、冲突合并、遗忘 | 敏感内容不自动写入；支持彻底删除 | 2 天 |
| CTX-01 | ContextBuilder | 统一组装安全规则、画像、计划、记忆和 RAG | 每段上下文带来源、优先级和截断策略 | 2-3 天 |
| CTX-02 | Token Budget | 控制历史、记忆和知识的 Token 占用 | 超预算时按优先级压缩，不丢安全上下文 | 1-2 天 |
| RAG-01 | Ingestion | Markdown/JSON 文档导入与分块 | 可重复构建索引，支持文档版本和来源 | 2-3 天 |
| RAG-02 | Retrieval | 关键词 + 向量的混合检索 | 对标注问题集计算 Recall@K | 3 天 |
| RAG-03 | Rerank | 去重、重排和引用返回 | Chat API 返回实际使用的知识片段与来源 | 2 天 |
| MAG-01 | Agent Protocol | `AgentTask`、`AgentResult`、`AgentRegistry` | 所有专家 Agent 使用统一输入输出 | 2 天 |
| MAG-02 | Expert Agents | Coach、Planner、Reporter、Adjustment | 每个 Agent 有明确职责和工具白名单 | 3-4 天 |
| MAG-03 | Supervisor | 任务分类、Agent 分派、结果汇总 | 典型问题路由准确率达到目标 | 3 天 |
| MAG-04 | Shared Context | 共享只读上下文和任务状态 | Agent 间不通过自由文本传递核心业务对象 | 2 天 |
| MAG-05 | HITL | 计划和调整建议进入 Proposal | 未经确认不得变更正式计划 | 1-2 天 |
| OBS-01 | Trace | 记录 Agent、Tool、耗时、状态和错误 | 每个请求可通过 trace_id 完整回放 | 2-3 天 |
| OBS-02 | Usage | 记录 Provider、Model、Token 和调用次数 | 可按请求和用户查看模型调用成本 | 1-2 天 |
| EVA-01 | Eval Dataset | 建立安全、路由、工具、RAG、记忆测试集 | 至少 50 条人工标注用例 | 2-3 天 |
| EVA-02 | Metrics | 安全通过率、路由准确率、Recall@K、工具成功率 | 一条命令生成 JSON 和 Markdown 报告 | 2-3 天 |
| EVA-03 | Regression | 将评估集接入 CI | Prompt、模型或检索改动可发现性能回退 | 2 天 |

### 6.2 P1：增强展示能力

| 编号 | 模块 | 待实现内容 | 验收标准 | 预计工作量 |
|---|---|---|---|---:|
| LLM-01 | Provider | 完成真实 OpenAI-compatible Provider | DashScope/OpenAI-compatible/Fake 可配置切换 | 2 天 |
| LLM-02 | Streaming | 流式模型输出和前端增量渲染 | Coach 页面可显示逐步响应 | 2-3 天 |
| TOOL-01 | Schema | 完整工具参数 Schema 与校验错误 | 非法参数不会进入领域逻辑 | 1-2 天 |
| TOOL-02 | Events | Tool 调用前后监听器 | Trace 可记录输入摘要、输出摘要和耗时 | 1-2 天 |
| TOOL-03 | Async | 独立查询类工具并行执行 | 周报/知识/记忆检索可并行且支持超时 | 2-3 天 |
| MCP-01 | MCP Client | 接入一个与健身相关的 MCP 工具 | Agent 可通过 MCP 查询结构化数据 | 2-3 天 |
| MCP-02 | MCP Server | 将 FitFlow 知识检索封装成 MCP Server | 可被独立 Agent 客户端调用 | 3 天 |
| REF-01 | Reflection | 对低置信度回答进行一次反思修正 | 有最大迭代次数，安全规则不可被修改 | 2 天 |
| UI-01 | Progress | 展示 Agent、工具和审批进度 | 用户能看到当前执行阶段和失败原因 | 2-3 天 |
| UI-02 | Export | 导出训练计划和周报 | 支持 Markdown 或 PDF | 1-2 天 |
| ENG-01 | Docker | 后端和前端容器化 | `docker compose up` 可启动完整项目 | 2 天 |
| ENG-02 | CI | GitHub Actions 测试与评估 | PR 自动运行单元测试和核心评估集 | 1-2 天 |

### 6.3 P2：秋招后的研究方向

| 编号 | 模块 | 方向 | 处理建议 |
|---|---|---|---|
| A2A-01 | A2A | 跨进程 Agent 通信 | 先保留接口设计，不在秋招主线实现 |
| ANP-01 | ANP | Agent 服务发现 | 只写调研文档 |
| RL-01 | Agentic RL | SFT/GRPO 优化路由或工具选择 | 有高质量数据集后再开始 |
| KG-01 | Knowledge Graph | Neo4j 语义记忆 | 仅当现有向量检索无法满足关系查询时引入 |
| MM-01 | Multimodal | 健身动作视频理解 | 作为后续独立项目，不并入当前主线 |

## 7. 八周冲刺安排

当前日期为 2026-07-28。建议在 2026-09-22 前完成可投递版本。

| 周次 | 日期 | 核心任务 | 交付物 |
|---|---|---|---|
| W1 | 07-29 至 08-04 | 架构整理、Ports、依赖注入、模型拆分 | 新目录、架构图、全部旧测试通过 |
| W2 | 08-05 至 08-11 | Working/Episodic/Semantic Memory | MemoryManager、记忆 API、隔离测试 |
| W3 | 08-12 至 08-18 | ContextBuilder、Token Budget、记忆策略 | 可解释上下文、来源记录、截断测试 |
| W4 | 08-19 至 08-25 | 文档导入、Embedding、混合检索、重排 | RAG Pipeline、标注问题集、Recall@K |
| W5 | 08-26 至 09-01 | Expert Agents、Supervisor、SharedContext | 多 Agent 路由与协作 Demo |
| W6 | 09-02 至 09-08 | Trace、Token/成本、离线评估和 CI | Eval 报告、调用链页面或日志 |
| W7 | 09-09 至 09-15 | MCP、流式输出、Docker | MCP Demo、实时进度、Compose |
| W8 | 09-16 至 09-22 | Bug 修复、文档、录屏、简历和面试材料 | Release、演示视频、项目介绍和问答稿 |

### 7.1 时间不足时的裁剪顺序

按以下顺序从后向前裁剪：

1. Reflection。
2. 自定义 MCP Server。
3. PDF 导出。
4. OpenAI-compatible Provider。
5. 异步工具执行。

以下内容不能裁剪：

- Safety Guard。
- MemoryManager。
- ContextBuilder。
- Supervisor 与 Agent Protocol。
- RAG 评估。
- Trace 与自动化测试。

## 8. 评估指标

| 维度 | 指标 | 秋招目标 |
|---|---|---:|
| 安全 | 高风险问题拦截率 | 100% |
| 安全 | 未确认计划写入正式数据次数 | 0 |
| 隔离 | 跨用户记忆泄漏 | 0/100 |
| 路由 | Supervisor Agent 路由准确率 | ≥ 90% |
| 工具 | Tool 参数校验和执行成功率 | ≥ 95% |
| RAG | 标注问题集 Recall@5 | ≥ 85% |
| RAG | 回答引用覆盖率 | ≥ 90% |
| 记忆 | 应召回长期偏好的命中率 | ≥ 90% |
| 稳定性 | 核心离线回归测试通过率 | 100% |
| 可观测性 | 带完整 trace_id 的 Agent 请求 | 100% |
| 成本 | 可统计 Token/调用次数的真实模型请求 | 100% |

指标需要附带数据集规模、测试环境和计算方法，不能只在 README 写结论。

## 9. 秋招作品集交付清单

### 9.1 GitHub 仓库

- 清晰的中文和英文 README。
- 系统架构图、多 Agent 时序图、记忆流转图。
- 一条命令启动方式。
- `.env.example`，不包含真实密钥。
- Docker Compose。
- GitHub Actions 状态。
- 单元测试、集成测试和 Agent 评估报告。
- Demo 数据初始化脚本。
- 设计决策文档 ADR。

### 9.2 演示材料

- 3 分钟完整 Demo 视频。
- 30 秒项目概览版本。
- 安全拦截 Demo。
- 多 Agent 协作 Demo。
- 跨会话记忆 Demo。
- RAG 引用 Demo。
- 人工确认计划调整 Demo。
- Trace 或评估报告截图。

### 9.3 简历可写方向

下面内容只能在对应功能和指标真正实现后写入简历：

1. 设计安全约束的多 Agent 健身教练，使用 Supervisor 协调计划、报告和调整 Agent，通过类型化任务协议与工具白名单控制协作边界。
2. 实现 Working、Episodic、Semantic 三层记忆与 ContextBuilder，支持跨会话偏好召回、时间衰减、重要性排序和用户级隔离。
3. 构建健身知识混合 RAG，支持文档分块、Embedding、关键词与向量融合、重排和引用追踪，并在人工标注集上达到可复现指标。
4. 将确定性安全规则和 LLM 生成解耦，通过 Proposal + Human-in-the-loop 保证未经确认的计划调整不会进入正式数据。
5. 建立 Agent Trace 与离线评估体系，覆盖路由准确率、工具成功率、RAG Recall@K、安全拦截和模型调用成本。

## 10. 面试重点准备

需要能够回答：

### 架构

- 为什么选择模块化单体而不是微服务？
- Agent、Application、Domain、Infrastructure 如何解耦？
- 为什么 Tool 依赖 Ports 而不是直接依赖 SQLite？
- 如何替换 DashScope 而不修改业务逻辑？

### 记忆

- Working、Episodic、Semantic Memory 的区别是什么？
- 哪些信息不应该自动写入长期记忆？
- 如何处理记忆冲突、过期和用户删除？
- 如何防止跨用户记忆泄漏？

### RAG

- 为什么关键词检索不够？
- Chunk Size、Overlap 和 Top-K 如何选择？
- 如何衡量检索质量而不是只看最终回答？
- 向量检索、BM25、重排分别解决什么问题？

### 多 Agent

- 为什么需要 Supervisor，而不是一个大 Prompt？
- 如何防止 Agent 无限互相调用？
- 如何定义共享上下文和任务结果？
- 哪些步骤必须由用户确认？

### 安全与评估

- 为什么风险判断不能交给 LLM？
- 如何保证模型升级不会破坏安全行为？
- 如何设计 Agent 路由和工具调用评估集？
- 如何记录 Token、费用、延迟和失败节点？

## 11. 风险与应对

| 风险 | 表现 | 应对 |
|---|---|---|
| 范围过大 | 目录很多但功能不可运行 | 每阶段必须有 API、测试和 Demo |
| 过度模仿 HelloAgents | 实现与健身场景无关的模块 | 以业务闭环和面试价值决定优先级 |
| LLM 决定安全 | 输出不可预测 | Safety Guard 始终使用确定性规则 |
| 多 Agent 形式化 | 多个 Agent 只是重复调用模型 | 明确角色、工具、输入输出和评估指标 |
| 记忆污染 | 错误内容长期保存 | 写入策略、来源、置信度、确认和删除 |
| RAG 无评估 | 只能展示几个成功示例 | 建立标注集和 Recall@K |
| 测试产生费用 | CI 调用真实模型 | 测试强制 Fake Provider，真实调用单独评估 |
| 密钥泄漏 | `.env` 被提交 | Secret Scan、`.gitignore` 和 CI 检查 |

## 12. 推荐的下一次开发迭代

第一轮只做架构整理，不新增多 Agent：

1. 建立 `application`、`ai`、`ports`、`bootstrap`。
2. 将现有 Agent 移动到 `ai/agents/single`。
3. 将 LLM Provider 移动到 `infrastructure/llm`。
4. 将 Repository 拆为 Port 与 SQLite 实现。
5. 建立依赖注入 Container。
6. API 改为调用 Application Use Case。
7. 保证当前 100 个测试继续通过。
8. 增加架构依赖测试，防止层级再次混乱。

完成这一轮后，再进入 MemoryManager 和 ContextBuilder。这样每一次提交都能运行、能测试、能讲清楚，也最适合作为秋招项目持续展示。

