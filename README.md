# FitFlow AI

FitFlow AI 是一个面向个人训练场景的 AI 健身教练项目。前端使用 React PWA，后端使用 FastAPI，PostgreSQL 保存账号和业务数据，Redis 保存登录会话与短期工作记忆。

训练画像、风险判断和计划安全校验由后端规则执行。AI 教练在回答和生成计划前读取当前用户的画像、正式计划、长期记忆与本地知识，并在这些数据组成的上下文中工作。

## 已实现功能

- 邮箱注册和登录，使用 HttpOnly Cookie 与 Redis Session 维持登录状态
- 用户训练画像和健康风险检查
- AI 教练对话与长期记忆查询
- 下周训练计划生成、修改、确认和同步
- 正式训练计划及历史版本查询
- 训练记录和训练周报
- 中文动作库与动作详情页面
- 多用户数据隔离

## 技术组成

| 部分 | 技术 |
| --- | --- |
| 前端 | React、TypeScript、Vite、PWA |
| API | FastAPI |
| AI 编排 | LangGraph |
| 数据访问 | SQLAlchemy、asyncpg、Alembic |
| 业务数据与长期记忆 | PostgreSQL |
| 登录会话与短期记忆 | Redis |
| 自动化测试 | Pytest |

项目目录和请求链路见 [项目结构](docs/项目结构.md)。

## 环境要求

- Python 3.11 或更高版本
- Node.js 与 npm
- Docker Desktop
- Conda 环境 `fitflow`，也可以使用其他独立的 Python 3.11 环境

## 本地启动

### 1. 启动 PostgreSQL 和 Redis

在项目根目录执行：

```powershell
docker compose up -d postgres redis
docker compose ps
```

### 2. 启动后端

```powershell
conda activate fitflow
Set-Location backend
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

如果 `backend/.env` 已存在，请保留原文件并检查其中的配置，不要再次覆盖。

后端启动后可访问：

- 健康检查：`http://127.0.0.1:8000/health`
- API 文档：`http://127.0.0.1:8000/docs`

### 3. 启动前端

另开一个终端，在项目根目录执行：

```powershell
Set-Location web
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。Vite 会把 `/api` 和 `/health` 请求代理到本机的 FastAPI 服务。

## 大模型配置

后端启动时读取 `backend/.env`。项目支持 `fake`、`dashscope`、`siliconflow` 和 `openai`，`.env.example` 当前使用 SiliconFlow：

```env
FITFLOW_LLM_PROVIDER=siliconflow
SILICONFLOW_MODEL=Qwen/Qwen3.5-4B
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_API_KEY=填写你的API密钥
```

真实密钥只应保存在被 Git 忽略的 `backend/.env` 中。测试环境强制使用 Fake Provider，不会请求真实模型。

## 数据与登录会话

用户账号、训练画像、长期记忆、训练计划、计划提案和训练记录保存在 PostgreSQL。密码使用 Argon2id 哈希，API 不返回密码哈希。

登录成功后，后端将不透明令牌写入 HttpOnly Cookie。Redis 只保存令牌摘要与用户 ID 的关联，并按照配置的空闲时间自动过期。

本地开发使用以下配置：

```env
FITFLOW_SESSION_BACKEND=redis
FITFLOW_SESSION_TTL_SECONDS=604800
FITFLOW_SESSION_COOKIE_NAME=fitflow_session
FITFLOW_SESSION_COOKIE_SECURE=false
```

通过 HTTPS 部署时，将 `FITFLOW_SESSION_COOKIE_SECURE` 设置为 `true`，并通过同一站点提供前端页面和 `/api`。PostgreSQL 的 `5432` 端口和 Redis 的 `6379` 端口只应对后端所在的可信网络开放。

## 验证

后端测试：

```powershell
Set-Location backend
python -m pytest -q
```

前端检查与构建：

```powershell
Set-Location web
npm run typecheck
npm run build
```

## 文档

- [项目结构](docs/项目结构.md)
- [对话式训练计划升级设计](docs/conversational-training-plan-upgrade-design.md)
- [对话式训练计划十步实施计划](docs/conversational-training-plan-10-step-implementation-plan.md)
- [长期记忆设计](docs/fitflow-long-term-memory-design.md)
- [多用户 Cookie Session 实施说明](docs/multi-user-cookie-session-implementation.md)
- [开发计划](docs/fitflow-ai-autumn-development-plan.md)

## 安全边界

- 胸痛、急性损伤等高风险标记会阻止自动生成训练计划。
- 初学者计划需要通过训练天数、动作数量和 RPE 等后端校验。
- 未通过安全校验的计划不会保存为正式计划。
- 大模型不负责疾病诊断、康复处方或风险等级判断。
- API 根据登录会话取得用户身份，并用用户 ID 隔离业务数据。
