# 创建 LangGraph Checkpointer（PostgresSaver）专用的异步 Postgres 连接池。
# LangGraph 要把 State 状态快照持久存到 PostgreSQL 数据库，不能每次新建连接，用连接池管理数据库连接。

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import get_settings


def create_langgraph_pool() -> AsyncConnectionPool:
    settings = get_settings()

    return AsyncConnectionPool(
        conninfo=settings.langgraph_database_url,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
            "prepare_threshold": 0,
        },
    )