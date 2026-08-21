# 怎么连接数据库

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


settings = get_settings()


# 创建 SQLAlchemy 异步数据库引擎
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)


# 创建 AsyncSession 工厂  创建一次数据库工作操作台的工厂
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    为每个请求创建一个独立的数据库 Session。
    请求结束后自动释放 Session。
    """
    async with SessionLocal() as session:
        yield session


async def check_database() -> str | None:
    """
    检查 PostgreSQL 连接，并获取 pgvector 扩展版本。
    """
    async with engine.connect() as connection:

        # 1. 验证 PostgreSQL 是否可连接
        await connection.execute(
            text("SELECT 1")
        )

        # 2. 查询 pgvector 扩展版本
        result = await connection.execute(
            text(
                """
                SELECT extversion
                FROM pg_extension
                WHERE extname = 'vector'
                """
            )
        )

        return result.scalar_one_or_none()