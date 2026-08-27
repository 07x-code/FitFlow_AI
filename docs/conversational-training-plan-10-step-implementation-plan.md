# 对话式训练计划功能：10 步教学实施计划

> 更新日期：2026-08-19  
> 实施方式：用户亲自编写代码，Codex 逐个检查点讲解、审查和验证  
> 设计依据：[对话式训练计划升级方案](./conversational-training-plan-upgrade-design.md)  
> 总体规划：[FitFlow AI 秋招分步开发计划](./fitflow-ai-autumn-development-plan.md)

## 使用规则

这份计划分为 10 个大步骤。每个大步骤继续拆成若干小检查点，一次只做一个检查点。

每个检查点按下面的方式推进：

1. Codex 先说明这一小步解决什么问题，并给出需要编写的代码。
2. 用户亲自修改文件并运行指定命令。
3. 用户把命令输出或代码发给 Codex。
4. Codex 检查代码、解释错误并给出修正建议。
5. 当前检查点通过后，才进入下一小步。

实现过程中不提前引入后续步骤的抽象，不同时重构无关模块。正式业务数据库最终只保留 PostgreSQL，Redis 只负责短期状态。

## 第 1 步：建立 PostgreSQL 本地开发环境

### 目标

使用 Docker Compose 启动固定版本的 PostgreSQL，并准备相互隔离的开发库、测试库和演示库。

### 小检查点

- [x] 1.1 创建最小 `compose.yaml`，配置固定 PostgreSQL 镜像、用户、密码和开发库。
- [x] 1.2 增加 Docker 数据卷和 PostgreSQL 健康检查。
- [x] 1.3 增加初始化 SQL，创建 `fitflow_test` 和 `fitflow_demo`。
- [x] 1.4 在 `backend/.env.example` 中增加开发、测试和演示数据库连接地址。
- [x] 1.5 首次启动容器，等待健康状态变为 `healthy`。
- [x] 1.6 使用 `psql` 分别连接三个数据库并执行 `SELECT 1`。
- [x] 1.7 练习停止和重新启动容器，确认数据卷仍然存在。

### 验收

- `docker compose ps` 显示 PostgreSQL 为 `healthy`。
- `fitflow_dev`、`fitflow_test` 和 `fitflow_demo` 都能连接。
- 删除并重建普通容器不会丢失数据卷中的数据。
- 项目中没有真实生产密码。

## 第 2 步：建立异步数据库连接基础

### 目标

让 FastAPI 能通过 SQLAlchemy 2.x Async 和 asyncpg 连接 PostgreSQL，但暂时不迁移业务 Repository。

### 小检查点

- [x] 2.1 安装并固定 `SQLAlchemy`、`asyncpg` 和 `alembic` 依赖。
- [x] 2.2 在 `AppSettings` 中增加 `database_url`，并校验配置不能为空。
- [x] 2.3 创建异步 Engine 和 `async_sessionmaker`。
- [x] 2.4 使用 FastAPI lifespan 在启动时创建数据库资源，在关闭时释放 Engine。
- [x] 2.5 编写最小连接检查，执行 `SELECT 1`。
- [x] 2.6 为测试环境读取独立的 `FITFLOW_TEST_DATABASE_URL`。

### 验收

- FastAPI 启动时可以连接 `fitflow_dev`。
- 应用关闭时数据库连接池被正常释放。
- 测试代码不会连接开发库。
- 数据库连接失败时应用给出明确错误，不静默回退 SQLite。

## 第 3 步：引入 Alembic 并建立业务 Schema

### 目标

用 Alembic 管理 PostgreSQL Schema，不再由各个 Repository 在运行时执行 `CREATE TABLE`。

### 小检查点

- [x] 3.1 初始化 Alembic，并让迁移读取统一数据库配置。
- [x] 3.2 建立 SQLAlchemy Base 和第一张 `fitness_profiles` 表。
- [x] 3.3 生成并人工检查第一份迁移。
- [x] 3.4 增加训练计划、Proposal、训练记录和长期记忆表。
- [x] 3.5 为用户隔离、状态、时间和常用查询增加索引。
- [x] 3.6 增加外键、唯一约束、非空约束和删除策略。
- [x] 3.7 验证 `upgrade`、`downgrade` 和从空数据库重新 `upgrade`。

### 验收

- 新数据库可以只靠 Alembic 从零建表。
- PostgreSQL 业务表只由 Alembic 创建；旧 SQLite Repository 的运行时建表逻辑暂时保留，并在 4.8 删除。
- 迁移可以回退并重新执行。
- Schema 中不存在 SQLite 专用语法。

## 第 4 步：将 Repository 迁移到 PostgreSQL Async

### 目标

逐个替换 SQLite Repository，并把相关 Port、Use Case 和 API 调整为异步调用。

> 执行顺序调整（2026-08-19）：4.1 和 4.2 已完成。由于 `training_plans` 要求目标周、版本、状态和必填的 `source_proposal_id`，而当前领域模型尚未提供这些数据，4.3 至 4.8 暂停。先完成第 6 步的训练计划与 Proposal 领域模型升级，再从 4.3 恢复 Repository 迁移。

### 小检查点

- [x] 4.1 先迁移 `ProfileRepository`，完成保存、查询和用户隔离测试。
- [x] 4.2 迁移 `UserMemoryRepository`。
- [ ] 4.3 迁移 `TrainingPlanRepository`。
- [ ] 4.4 迁移 `TrainingPlanProposalRepository`。
- [ ] 4.5 迁移 `WorkoutSessionRepository` 和周报查询。
- [ ] 4.6 将 Repository Port、Use Case 和 FastAPI 路由改成 `async`。
- [ ] 4.7 更新依赖注入，让同一请求可以共享数据库 Session。
- [ ] 4.8 删除 SQLite Adapter、配置和测试夹具。

### 验收

- Repository 集成测试全部连接 `fitflow_test`。
- 每个测试结束后数据被回滚或清理。
- 运行代码只存在 PostgreSQL Repository 实现。
- 项目不再需要 `fitflow.db`。

## 第 5 步：完成长期记忆与短期记忆分工

### 目标

长期记忆保存在 PostgreSQL，当前会话和临时流程状态保存在 Redis。

### 小检查点

- [ ] 5.1 扩展长期记忆字段，加入状态、来源、确认时间和更新时间。
- [ ] 5.2 只允许保存用户明确输入或确认过的长期记忆。
- [ ] 5.3 实现长期记忆的查询、修改、软删除和用户隔离。
- [ ] 5.4 将 Redis Working Memory 改为异步客户端。
- [ ] 5.5 保留 `user_id + session_id` 键隔离、TTL 和容量上限。
- [ ] 5.6 增加 `awaiting_plan_decision` 会话流程状态。
- [ ] 5.7 处理 Redis 过期和不可用时的 PostgreSQL 恢复路径。

### 验收

- 长期偏好跨会话仍然存在。
- 临时消息不会自动进入长期记忆。
- 不同用户和不同会话之间没有记忆污染。
- 清空 Redis 不会删除 Proposal 或正式训练计划。

## 第 6 步：升级训练计划和 Proposal 领域模型

### 目标

让计划能表示具体自然周、日期和版本，让 Proposal 能保留修订历史。

> 当前执行入口：本步骤提前到 4.2 之后实施。6.1 至 6.7 完成后，返回 4.3 继续迁移 `TrainingPlanRepository`。

### 小检查点

- [ ] 6.1 为 `TrainingPlanDraft` 增加目标周、时区和计划摘要。
- [ ] 6.2 为训练日增加具体日期、重点和预计时长。
- [ ] 6.3 为正式计划增加版本、状态和 `source_proposal_id`。
- [ ] 6.4 为 Proposal 增加 operation、revision、parent 和 base plan 字段。
- [ ] 6.5 增加 pending、approving、approved、rejected、superseded 状态转换规则。
- [ ] 6.6 增加同一用户同一周的正式计划唯一约束。
- [ ] 6.7 关闭 `TrainingPlanAgent -> save_training_plan` 的直接写入路径。

### 验收

- 每个正式计划都能追溯到一个已批准 Proposal。
- 修订 Proposal 不覆盖旧版本。
- superseded Proposal 不能再次批准。
- 未批准 Proposal 不会出现在正式计划查询中。

## 第 7 步：构建计划上下文和确定性安全规则

### 目标

用统一的 ContextBuilder 提供计划所需数据，并在模型前后执行固定规则。

### 小检查点

- [ ] 7.1 定义 `PlanGenerationContext` 的结构化模型。
- [ ] 7.2 加载用户画像和健康限制。
- [ ] 7.3 加载目标周正式计划、近期训练记录和周报摘要。
- [ ] 7.4 只召回与计划相关的已确认长期记忆。
- [ ] 7.5 合并 Redis 当前会话和本轮修改反馈。
- [ ] 7.6 记录每段上下文的来源、更新时间和截断原因。
- [ ] 7.7 实现日期、训练量、RPE、动作白名单和恢复间隔校验。
- [ ] 7.8 信息不足时返回具体澄清问题，不生成 Proposal。

### 验收

- 本轮明确输入可以覆盖旧的非安全偏好。
- 安全规则不会被模型输出覆盖。
- 模型看不到无限历史和其他用户数据。
- 每次生成都能说明使用了哪些上下文来源。

## 第 8 步：实现结构化计划生成与修订工作流

### 目标

让大模型根据结构化上下文生成候选计划，但只能创建 Proposal。

### 小检查点

- [ ] 8.1 定义模型的结构化计划输出 Schema。
- [ ] 8.2 实现 create_plan、revise_plan 和 need_clarification 意图。
- [ ] 8.3 构建受控计划工作流：加载上下文、风险检查、生成、校验、创建 Proposal。
- [ ] 8.4 非法结构最多修复一次，不做无限 Reflection。
- [ ] 8.5 实现 `create_training_plan_proposal` 受控工具。
- [ ] 8.6 实现 `revise_training_plan_proposal`，记录 parent 和 revision。
- [ ] 8.7 防止同一用户同一周重复创建 pending Proposal。

### 验收

- 模型只能获得创建或修订 Proposal 的工具。
- 模型输出未通过规则时不会写入 Proposal。
- 用户修改意见会反映在新版本中。
- 模型超时、非法 JSON 和预算耗尽都有稳定响应。

## 第 9 步：打通批准事务、Coach API 和前端

### 目标

完成“对话生成、查看草案、要求修改、明确批准、同步计划”的产品闭环。

### 小检查点

- [ ] 9.1 实现 Proposal 批准 Unit of Work。
- [ ] 9.2 使用条件更新保证 pending Proposal 只能批准一次。
- [ ] 9.3 为批准、修订和放弃增加 `Idempotency-Key`。
- [ ] 9.4 扩展 `CoachChatResponse`，返回 Proposal action。
- [ ] 9.5 在 Coach 页面显示 Proposal 卡片。
- [ ] 9.6 增加“采用计划”“提出修改”“暂不采用”操作。
- [ ] 9.7 将训练计划页面从 Mock 数据切换到真实 API。
- [ ] 9.8 批准成功后刷新目标周正式计划。

### 验收

- 批准前正式计划表没有新增记录。
- 批准后计划页面能读取同一份计划。
- 修改后产生新 Proposal，旧版仍可审计。
- 按钮操作和自然语言操作共用同一应用用例。

## 第 10 步：测试、Trace、并发和最终交付

### 目标

证明功能安全、可追踪、可恢复，并能在并发请求下保持数据一致。

### 小检查点

- [ ] 10.1 补齐领域模型和安全规则单元测试。
- [ ] 10.2 补齐 PostgreSQL Repository 与事务集成测试。
- [ ] 10.3 建立 Coach 意图、工具选择和记忆召回 Eval。
- [ ] 10.4 Trace 记录上下文来源、模型调用、校验结果和 Proposal 状态变化。
- [ ] 10.5 测试 20 个请求同时批准一个 Proposal。
- [ ] 10.6 测试 Redis、LLM 和 PostgreSQL 故障与恢复。
- [ ] 10.7 使用 Fake Provider 和真实模型分别测试。
- [ ] 10.8 前后端运行 lint、测试和生产构建。
- [ ] 10.9 准备 Demo Seed 和完整演示脚本。
- [ ] 10.10 更新 README、架构图和最终验收记录。

### 验收

- 并发批准只生成一个正式计划。
- 高风险输入拦截率为 100%。
- 跨用户数据泄漏次数为 0。
- Redis 或 LLM 故障不会破坏正式业务数据。
- 新环境能根据文档启动并复现完整流程。

## 总体验收流程

最终 Demo 按下面的顺序完成：

```text
创建用户画像
  -> 保存明确长期偏好
  -> 在 Coach 中请求下周训练计划
  -> 查看模型生成的 Proposal
  -> 提出一次具体修改
  -> 查看有版本关系的新 Proposal
  -> 明确批准
  -> 在训练计划页面查看正式计划
  -> 完成训练并生成周报
  -> 通过 Trace 查看完整执行过程
```

完成一个大步骤后再进入下一个。任何一步没有通过自动化测试或手动验收，都不继续叠加后续功能。
