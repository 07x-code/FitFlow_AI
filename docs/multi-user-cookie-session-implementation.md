# FitFlow 多用户 Cookie Session 实施说明

## 目标状态

FitFlow 使用 PostgreSQL 保存用户账号，使用 Redis 保存登录会话。浏览器只持有
HttpOnly Cookie 中的不透明令牌，业务接口根据会话解析当前用户，并按用户标识
隔离训练画像、长期记忆、训练计划、提案和训练记录。
HttpOnly Cookie + Redis Session
## 请求链路

```text
React PWA
  → HttpOnly Cookie
  → FastAPI 当前用户依赖
  → Redis Session 获取 user_id
  → PostgreSQL 校验 active 用户
  → 用户级业务用例和 Repository 查询
```

Redis 键使用会话令牌的 SHA-256 摘要，Redis 数据中保存用户标识并设置滑动 TTL。
账号被禁用后，后端会拒绝已有会话并删除对应 Redis 键。

## 认证接口

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `POST` | `/api/auth/register` | 创建账号并建立登录会话 |
| `POST` | `/api/auth/login` | 校验邮箱密码并建立新会话 |
| `GET` | `/api/auth/me` | 恢复当前登录用户 |
| `POST` | `/api/auth/logout` | 删除当前会话并清除 Cookie |

注册密码长度为 8–128 个字符，数据库只保存 Argon2id 哈希。登录失败统一返回
相同响应，避免根据响应区分邮箱是否存在。

## Cookie 与 Redis 配置

```env
FITFLOW_REDIS_URL=redis://127.0.0.1:6379/0
FITFLOW_SESSION_BACKEND=redis
FITFLOW_SESSION_TTL_SECONDS=604800
FITFLOW_SESSION_COOKIE_NAME=fitflow_session
FITFLOW_SESSION_COOKIE_SECURE=false
```

Cookie 使用 `HttpOnly`、`SameSite=Lax` 和根路径。本地 HTTP 开发使用
`FITFLOW_SESSION_COOKIE_SECURE=false`；HTTPS 环境使用 `true`。

## 本地启动

```powershell
cd F:\python_project\FitFlow_AI
docker compose up -d postgres redis

cd backend
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

另开终端启动前端：

```powershell
cd F:\python_project\FitFlow_AI\web
npm install
npm run dev -- --host 0.0.0.0
```

Vite 将 `/api` 代理到 FastAPI，因此本地浏览器在同一站点下使用 Cookie。

## 云服务器要求

- PostgreSQL 和 Redis 只监听内网或容器网络，不直接暴露到公网。
- Nginx 或 Caddy 在同一个 HTTPS 域名下提供前端静态资源并反向代理 `/api`。
- 生产环境启用安全 Cookie，并使用独立的数据库与 Redis 密码。
- 部署前执行 `python -m alembic upgrade head`。
- 多个 FastAPI 实例共享同一 PostgreSQL 和 Redis，即可识别同一登录会话。

## 验证命令

```powershell
cd F:\python_project\FitFlow_AI\backend
python -m pytest -q
python -m alembic check

cd ..\web
npm run typecheck
npm run build
```
