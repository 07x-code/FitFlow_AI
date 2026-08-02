# MEM-01 工作记忆实现说明

完成日期：2026-07-31

## 1. 完成范围

本次只实现 Working Memory，不提前实现 Episodic Memory、Semantic Memory
或统一 MemoryManager。

已完成：

- 保存会话内的用户消息和助手回复。
- 保存工具调用后的 Observation 摘要。
- 使用 `user_id + session_id` 双重隔离。
- 支持 TTL 自动过期，默认 7200 秒。
- 支持容量限制，默认每个会话 40 条。
- 超出容量时，低重要性优先淘汰；重要性相同时先淘汰旧条目。
- 提供会话结束接口，立即清理当前用户的指定会话。
- AI Coach 会读取当前会话之前的工作记忆并加入提示词。
- 提供 Redis 正式适配器和进程内测试/本地适配器。

## 2. 代码分层

```text
backend/app/
├── domain/
│   ├── models/
│   │   ├── user_memory.py       # 用户主动保存的长期记忆模型
│   │   └── working_memory.py    # 会话工作记忆模型
│   └── policies/
│       └── working_memory.py    # 容量淘汰规则
├── ports/
│   └── working_memory.py    # WorkingMemoryStorePort
├── application/use_cases/
│   └── working_memory.py    # 查询和结束会话用例
├── infrastructure/memory/
│   ├── in_memory.py         # 无外部依赖的本地/测试实现
│   ├── redis_store.py       # Redis 实现
│   └── factory.py           # 根据配置选择实现
├── ai/agents/single/
│   └── coach.py             # 写入消息和 Observation，读取历史上下文
└── api/
    ├── coach.py             # 强制接收 X-Session-ID
    └── memories.py          # 查询和结束工作记忆会话
```

依赖方向：

```text
API → Application → Port ← Infrastructure
                  ↑
                Agent
                  ↓
                Domain
```

Agent 和 Application 都只依赖 `WorkingMemoryStorePort`，不知道底层是 Redis
还是进程内字典。

## 3. 数据模型

`WorkingMemoryItem` 的关键字段：

| 字段 | 作用 |
|---|---|
| `id` | 条目唯一标识 |
| `kind` | `message` 或 `tool_observation` |
| `role` | 消息角色：`user`、`assistant`、`system` |
| `tool_name` | Observation 对应的工具名 |
| `content` | 消息正文或脱敏后的工具摘要 |
| `created_at` | UTC 创建时间 |
| `importance` | 0 到 1 的重要性 |
| `metadata` | 预留的结构化元数据 |

Redis 键：

```text
fitflow:memory:working:{escaped_user_id}:{escaped_session_id}
```

底层使用 Redis Sorted Set，时间戳作为排序分数。追加、容量淘汰和刷新 TTL
通过一段 Lua 脚本原子执行，避免并发请求只完成其中一部分。

## 4. 请求与清理

AI Coach 请求：

```http
POST /api/coach/chat
X-User-ID: user-123
X-Session-ID: session-456
Content-Type: application/json

{"message": "RPE 是什么？"}
```

查询当前会话工作记忆：

```http
GET /api/memories/working/session-456
X-User-ID: user-123
```

结束会话并立即清理：

```http
DELETE /api/memories/working/session-456
X-User-ID: user-123
```

React PWA 在首次发送 Coach 消息时生成页面级 `session_id`，后续消息复用；
页面结束时使用 `keepalive` 请求调用清理接口。异常关闭或清理请求失败时，
Redis TTL 负责最终回收。

## 5. 配置

```env
FITFLOW_WORKING_MEMORY_BACKEND=redis
FITFLOW_REDIS_URL=redis://127.0.0.1:6379/0
FITFLOW_WORKING_MEMORY_TTL_SECONDS=7200
FITFLOW_WORKING_MEMORY_CAPACITY=40
```

- `redis`：正式 Redis 实现。
- `memory`：进程内实现，适合测试和没有 Redis 的本地演示。

当前代码默认使用 `memory`，所以未安装 Redis 客户端时原项目仍可运行。
要验证正式 Redis 实现，在项目的 Conda 环境中执行：

```powershell
conda activate fitflow
python -m pip install redis==8.0.1
```

本次修改没有执行上述安装命令，也没有修改 `base` 环境。

## 6. 为什么这样拆

1. `domain` 只描述“记忆是什么、如何淘汰”，不依赖 Redis。
2. `port` 固定 Agent 所需的最小操作，后续更换 Redis 客户端不影响 Agent。
3. Redis 解决多进程共享、TTL 和高频会话读写；SQLite 不适合承担短生命周期缓存。
4. `user_id + session_id` 同时进入存储键，避免不同用户和同一用户并发会话串线。
5. Observation 只保存摘要，不直接保存完整画像和工具原始输出，降低敏感数据泄漏与上下文膨胀风险。
6. 页面主动清理与 TTL 兜底同时存在，正常结束立即释放，异常结束最终也会回收。

## 7. 学习顺序

按以下顺序阅读代码：

1. `domain/models/working_memory.py`：先看一条工作记忆包含什么。
2. `domain/policies/working_memory.py`：理解容量超限时保留和淘汰哪些条目。
3. `ports/working_memory.py`：理解上层只允许使用的三个操作。
4. `infrastructure/memory/in_memory.py`：用最简单实现理解 TTL、容量和隔离。
5. `infrastructure/memory/redis_store.py`：再看相同契约如何映射到 Redis。
6. `ai/agents/single/coach.py`：看消息、Observation 如何写入，历史如何进入 Prompt。
7. `api/memories.py`：看会话如何显式结束。
8. `tests/test_working_memory.py` 和 `tests/test_working_memory_api.py`：用验收测试反推设计。

## 8. 验收测试

已覆盖：

- 不同用户、不同会话互不共享。
- TTL 到期后读取为空。
- 会话结束后立即清空。
- 超容量时按重要性和时间淘汰。
- Redis 键转义、TTL、容量和删除行为。
- Coach 写入消息和工具 Observation。
- 缺少 `X-Session-ID` 时返回 422。
- 原有 Coach、长期记忆、Container 和架构依赖测试继续通过。
