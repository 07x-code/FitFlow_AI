# FitFlow AI

FitFlow AI 是一个安全优先的 AI 健身教练项目。React PWA 是唯一前端，
FastAPI 后端负责应用用例、确定性安全规则、Agent 编排、记忆和数据持久化。

风险判断、训练计划生成和安全校验均由确定性规则执行；LLM 只解释已经通过
安全校验的上下文，不能绕过规则。

## 项目结构

```text
FitFlow_AI/
├── backend/
│   ├── app/
│   │   ├── api/                         # FastAPI 路由和依赖
│   │   ├── application/use_cases/       # 应用业务入口
│   │   ├── domain/                      # 领域层
│   │   │   ├── models/                 # 领域数据模型
│   │   │   └── policies/               # 数据筛选、淘汰与约束策略
│   │   ├── ai/
│   │   │   ├── agents/                  # Coach、Planner
│   │   │   ├── core/                    # Agent 基类和 Message
│   │   │   ├── tools/                   # Tool 和 ToolRegistry
│   │   │   ├── orchestration/           # LangGraph 编排
│   │   │   └── services/                # AI 解释服务
│   │   ├── ports/                       # Repository、LLM、Memory 接口
│   │   ├── infrastructure/
│   │   │   ├── persistence/postgres/    # PostgreSQL Repository 实现
│   │   │   ├── auth/                    # Redis 登录会话
│   │   │   ├── memory/                  # Redis、内存工作记忆
│   │   │   ├── llm/                     # 千问、Fake LLM
│   │   │   └── knowledge/               # 本地知识检索
│   │   ├── bootstrap/                   # Container 和 Factory
│   │   ├── core/                        # 环境配置
│   │   ├── data/                        # 本地知识文件
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── web/                                 # 唯一前端：React PWA
├── data/                                # 动作数据构建文件
├── docs/
├── README.md
└── pytest.ini
```

请求链路：

```text
React PWA
  → FastAPI API
  → Application UseCase
  → Domain / AI Agent
  → Port
  → Infrastructure
  → PostgreSQL / Redis / LLM Provider
```

## 环境要求

- Conda 环境：`fitflow`
- Python 3.11+
- Node.js 与 npm
- Docker Desktop

## 启动后端

```powershell
conda activate fitflow
cd F:\python_project\FitFlow_AI
docker compose up -d postgres redis
cd F:\python_project\FitFlow_AI\backend
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

API 文档：`http://127.0.0.1:8000/docs`

## 启动 React PWA

另开一个终端：

```powershell
cd F:\python_project\FitFlow_AI\web
npm install
npm run dev
```

生产构建：

```powershell
npm run build
```

## LLM 配置

后端自动读取 `backend/.env`：

```env
FITFLOW_LLM_PROVIDER=dashscope
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=你的 DashScope Key
```

真实密钥只保存在被 Git 忽略的 `.env`；自动化测试强制使用 Fake Provider，
不会访问真实模型或产生费用。

## 多用户登录

用户账号保存在 PostgreSQL，密码使用 Argon2id 哈希。登录成功后，后端生成
不透明会话令牌并写入 HttpOnly Cookie，会话本体保存在 Redis。业务 API 从
会话中解析用户身份，并以用户标识隔离画像、计划、记忆和训练记录。

本地开发配置：

```env
FITFLOW_SESSION_BACKEND=redis
FITFLOW_SESSION_TTL_SECONDS=604800
FITFLOW_SESSION_COOKIE_NAME=fitflow_session
FITFLOW_SESSION_COOKIE_SECURE=false
```

通过 HTTPS 部署时必须设置 `FITFLOW_SESSION_COOKIE_SECURE=true`，并让反向代理
在同一站点下提供 React 页面和 `/api`。

## 测试

```powershell
cd F:\python_project\FitFlow_AI
conda run -n fitflow python -m pytest backend/tests -q
```

## 安全边界

- 胸痛、急性损伤等高风险标记会阻止自动生成计划。
- 初学者计划必须通过训练天数、动作数量和 RPE 等安全校验。
- 未通过安全校验的计划不能保存。
- LLM 不负责疾病诊断、康复处方或风险等级判断。
- 用户身份由 Redis Session 和 HttpOnly Cookie 校验。
- 账号密码只以 Argon2id 哈希形式持久化。
