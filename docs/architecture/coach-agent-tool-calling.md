# AI Coach 受控工具调用架构

## 1. 改造目标

AI Coach 不再在每次请求中固定读取训练计划、长期记忆和健身知识。
后端只固定加载用户画像并执行确定性风险评估，其余上下文由千问根据问题按需调用只读工具。

本次改造遵循三个边界：

- 安全规则、身份认证和权限判断由后端执行。
- 大模型只负责决定是否需要额外信息，以及选择白名单只读工具。
- 修改计划、画像、记忆和训练记录的写工具暂不向大模型开放。

## 2. 调用流程

    用户问题
    -> 后端加载用户画像
    -> 确定性风险评估
       -> 风险阻止：返回固定安全提示
       -> 风险通过：Coach Agent 调用千问
          -> 无需工具：生成最终回答
          -> 产生 tool_calls
             -> 工具白名单和 Pydantic 参数校验
             -> 后端注入 user_id 和 session_id
             -> 执行只读工具并生成 Observation
             -> 写入 Working Memory
             -> 返回 Coach Agent
          -> 达到调用上限：关闭工具并强制收尾

## 3. 当前工具白名单

| 工具 | 模型可见参数 | 后端隐藏注入 | 用途 |
|---|---|---|---|
| get_latest_training_plan | 无 | user_id、session_id | 按需读取最近训练计划 |
| recall_user_memory | 无 | user_id、session_id | 按需读取长期偏好和限制 |
| retrieve_fitness_knowledge | query、limit | 无 | 按需检索本地健身知识 |

模型无法传入 user_id。即使模型构造额外的 user_id 参数，Pydantic 的
extra="forbid" 也会拒绝执行，因此不能借助工具查询其他用户的数据。

## 4. 固定安全流程

以下步骤不由模型选择，始终在进入工具调用图之前执行：

1. 使用请求头中的可信 X-User-ID 加载用户画像。
2. 使用领域层确定性规则执行健康风险评估。
3. 风险等级不允许自动建议时，直接返回固定安全回复。
4. 风险通过后，才允许千问看到只读工具定义。

工具执行过程中还会执行：

- 工具名称白名单校验。
- Pydantic 参数结构、长度和范围校验。
- 最大五轮工具调用限制。
- 内部异常脱敏，不向模型返回数据库或堆栈信息。
- 工具调用摘要写入当前用户、当前会话的 Working Memory。

## 5. 代码职责

    backend/app/
    ├── ai/
    │   ├── agents/single/coach.py
    │   │   └── 固定安全门禁、构建初始上下文、组装 API 响应
    │   ├── orchestration/coach_tool_graph.py
    │   │   └── model -> tools -> model 循环、次数限制、强制收尾
    │   └── tools/coach.py
    │       └── 工具 Schema、参数校验、身份注入、结果压缩
    ├── ports/llm.py
    │   └── 与模型厂商无关的消息、工具和 tool_call 类型
    └── infrastructure/llm/provider.py
        └── DashScope OpenAI 兼容请求与 tool_calls 解析

领域层和 Repository 不依赖 LangGraph 或 DashScope。工具层只通过现有
ToolRegistry 调用已装配的能力。

## 6. 千问请求形式

DashScopeLLMProvider.complete_with_tools 使用 OpenAI 兼容接口：

    POST /compatible-mode/v1/chat/completions

请求中发送标准 messages、tools 和 tool_choice="auto"。千问返回
tool_calls 后，后端校验并执行工具，再将结果作为 role="tool" 消息回传。
不需要新增 Python 依赖。

## 7. 测试覆盖

- 工具 Schema 不包含 user_id 和 session_id。
- 可信用户身份由后端注入，模型无法覆盖。
- 普通问候不会读取训练计划、长期记忆或知识库。
- 非法参数和白名单外工具不会执行。
- 重复调用在最大轮数处停止。
- DashScope 工具定义请求和 tool_calls 响应能够正确序列化、解析。
- 原有 AI Coach、RAG、Working Memory 和风险阻断测试保持通过。

## 8. 后续扩展

下一阶段可以增加只读工具：

- get_workout_history
- get_progress_report
- get_active_proposal

写操作不能直接开放为 save_* 或 update_*。应先设计：

    Agent 生成变更 proposal
    -> 后端规则校验
    -> 前端展示
    -> 用户确认
    -> 应用层执行正式写入

这样能够保留 Agent 的主动性，同时保证正式训练数据始终受程序规则和用户确认控制。
