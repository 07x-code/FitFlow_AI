import asyncio
from app.core.config import AppSettings

from app.infrastructure.persistence.postgres.database import (
    check_database_connection,
    create_database_engine,
    create_session_factory,
    
)


DATABASE_URL = AppSettings.from_env().test_database_url


def test_creates_async_engine_and_session_factory():
    """
    验证数据库工厂创建异步 Engine 和对应的 Session 工厂。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)
    session_factory = create_session_factory(engine)
    session = session_factory()

    try:
        assert engine.url.drivername == "postgresql+asyncpg"
        assert engine.url.database == "fitflow_test"
        assert session.bind is engine
        assert session.sync_session.expire_on_commit is False
        
    finally:
        asyncio.run(session.close())
        asyncio.run(engine.dispose())


def test_database_connection_check_reaches_postgresql():
    """
    验证异步数据库引擎能够连接 PostgreSQL 测试库。

    :return: 无返回值。
    """
    engine = create_database_engine(DATABASE_URL)

    try:
        asyncio.run(check_database_connection(engine))
    finally:
        asyncio.run(engine.dispose())