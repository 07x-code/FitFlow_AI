from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_database_engine(database_url: str) -> AsyncEngine:
    """
    创建 PostgreSQL 异步数据库引擎。

    :param database_url: SQLAlchemy 异步数据库连接地址。
    :return: 配置完成的异步数据库引擎。
    """
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
    )

async def check_database_connection(engine: AsyncEngine) -> None:
    """
    连接数据库并执行最小可用性检查。

    :param engine: 要检查的异步数据库引擎。
    :return: 无返回值。
    """
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


        
def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """
    创建绑定到指定异步引擎的 Session 工厂。

    :param engine: 异步数据库引擎。
    :return: 用于创建 AsyncSession 的工厂。
    """
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )