from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.coach import router as coach_router
from app.api.errors import register_application_error_handlers
from app.api.memories import router as memories_router
from app.api.profiles import router as profiles_router
from app.api.proposals import router as proposals_router
from app.api.reports import router as reports_router
from app.api.training_plans import router as training_plans_router
from app.api.workouts import router as workouts_router
from app.core.config import AppSettings
from app.infrastructure.auth.session_store import create_session_store
from app.infrastructure.persistence.postgres.database import (
    check_database_connection,
    create_database_engine,
    create_session_factory,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    管理应用启动和关闭期间的数据库资源。

    :param app: 当前 FastAPI 应用实例。
    :return: 用于控制应用启动和关闭阶段的异步迭代器。
    """
    settings = AppSettings.from_env()
    engine = create_database_engine(settings.database_url)
    session_store = create_session_store(
        settings.session_backend,
        redis_url=settings.redis_url,
        ttl_seconds=settings.session_ttl_seconds,
    )
    try:
        session_factory = create_session_factory(engine)
        await check_database_connection(engine)
        await session_store.ping()

        app.state.settings = settings
        app.state.database_engine = engine
        app.state.session_factory = session_factory
        app.state.session_store = session_store
        yield
    finally:
        await session_store.close()
        await engine.dispose()


app = FastAPI(
    title="fitflow-api",
    lifespan=lifespan,
)
register_application_error_handlers(app)
app.include_router(auth_router)
app.include_router(coach_router)
app.include_router(memories_router)
app.include_router(profiles_router)
app.include_router(proposals_router)
app.include_router(reports_router)
app.include_router(training_plans_router)
app.include_router(workouts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "service": "fitflow-api",
        "status": "ok",
    }
