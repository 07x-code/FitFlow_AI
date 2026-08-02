# 项目结构收敛说明

完成日期：2026-08-01

## 1. 本次目标

本次只收敛目录和依赖方向，不修改业务规则、SQL、数据库结构或 API 行为。

完成内容：

- 删除旧 `frontend/` Streamlit 前端，只保留 `web/` React PWA。
- 删除只做重新导出的 `backend/app/agents/`。
- 删除职责宽泛且重复的 `backend/app/services/`。
- 删除旧 `backend/app/workflows/` 兼容入口。
- 将 LangGraph 编排从 Planner Agent 中拆到 `ai/orchestration/`。
- 将 LLM、知识检索和 SQLite Repository 移到明确的基础设施目录。
- 更新测试导入、Container、README、pytest 配置和架构约束测试。

## 2. 当前目录职责

```text
backend/app/
├── api/                              # HTTP 路由、Header、Depends
├── application/use_cases/            # 应用业务入口
├── domain/                           # 领域层
│   ├── models/                      # 领域数据模型
│   └── policies/                    # 数据筛选、淘汰与约束策略
├── ai/
│   ├── agents/single/                # Coach、Planner
│   ├── core/                         # Agent 基类与消息
│   ├── tools/                        # Tool、Registry
│   ├── orchestration/                # LangGraph 工作流
│   └── services/                     # AI 解释服务
├── ports/                            # Repository、LLM、Memory 接口
├── infrastructure/
│   ├── persistence/sqlite/           # SQLite Repository 实现
│   ├── memory/                       # Redis、内存工作记忆
│   ├── llm/                          # 千问、Fake Provider
│   └── knowledge/                    # 本地知识检索
├── bootstrap/                        # 依赖装配
├── core/                             # 环境配置
└── main.py
```

唯一前端：

```text
web/                                  # React + TypeScript + Vite + PWA
```

## 3. 文件迁移映射

| 原路径 | 当前路径 |
|---|---|
| `app/services/llm_provider.py` | `app/infrastructure/llm/provider.py` |
| `app/services/knowledge_retriever.py` | `app/infrastructure/knowledge/retriever.py` |
| `app/services/coach_explainer.py` | `app/ai/services/training_plan_explainer.py` |
| `app/workflows/training_plan_workflow.py` | 删除兼容入口；真实编排位于 `app/ai/orchestration/training_plan_graph.py` |
| `app/infrastructure/*_repository.py` | `app/infrastructure/persistence/sqlite/` |
| `app/agents/` | 删除；统一使用 `app/ai/` |

## 4. 依赖关系

```text
React PWA
  → FastAPI API
  → Application UseCase
  → Domain / AI Agent
  → Port
  → Infrastructure
  → SQLite / Redis / DashScope
```

关键限制：

- `domain` 不依赖 FastAPI、Agent 或基础设施。
- `ai` 只依赖 `domain` 和 `ports`，不导入 Redis、SQLite 或具体 LLM Provider。
- `api` 不实例化 Repository。
- `bootstrap` 是唯一集中装配具体实现的位置。
- SQLite Repository 只实现 `ports/repositories.py` 定义的契约。

## 5. 为什么这样改

1. 删除两套前端后，页面和接口联调只有一个入口，不再重复维护。
2. 删除重新导出模块后，导入路径直接指向真实实现，查代码不会在兼容文件间跳转。
3. `services` 被拆成 `ai/services` 与 `infrastructure`，目录名能直接表达职责和依赖方向。
4. LangGraph 与 Agent 分开后，Planner 负责输入输出，Graph 只负责流程节点和路由。
5. SQLite 实现集中后，`ports` 是接口、`persistence/sqlite` 是实现，层次更清楚。

## 6. 阅读顺序

1. `backend/app/bootstrap/container.py`：先看所有具体实现如何装配。
2. `backend/app/api/`：看 HTTP 请求如何进入应用用例。
3. `backend/app/application/use_cases/`：看单个业务入口。
4. `backend/app/ai/agents/single/`：看 Agent 只依赖哪些端口。
5. `backend/app/ai/orchestration/training_plan_graph.py`：看 LangGraph 节点与安全路由。
6. `backend/app/ports/`：看上层依赖的抽象。
7. `backend/app/infrastructure/`：最后看 SQLite、Redis、千问和知识检索实现。

## 7. 验收命令

```powershell
conda run -n fitflow python -m pytest backend/tests -q
cd web
npm run build
```

旧路径检查：

```powershell
rg "from app\.(agents|services|workflows)" backend
rg "frontend|streamlit" README.md backend web pytest.ini
```

## 8. Git 提交名

```text
refactor(architecture): remove legacy frontend and compatibility layers
```
