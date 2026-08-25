# Executor 使用专门的 PostgreSQL 只读账号text2sql_reader 他对数据库只有读取权限
# AI Text-to-SQL专用账号  PostgreSQL专用只读用户

from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from app.config import get_settings
from app.text2sql.sql_validator import (
    validate_sql,
)


class SQLExecutionRejectedError(ValueError):
    """
    SQL 在执行之前被安全层拒绝。
    """


class SQLExecutionError(RuntimeError):
    """
    SQL 已通过静态校验，
    但数据库执行阶段失败。
    """


class SQLExecutionResult(BaseModel):
    """
    Text-to-SQL 查询执行结果。
    """

    sql: str

    columns: list[str] = Field(default_factory=list)

    rows: list[dict[str, Any]] = Field(
        default_factory=list
    )

    row_count: int

    truncated: bool


@lru_cache
def get_text2sql_engine() -> AsyncEngine:
    """独立的数据库连接池"""
    settings = get_settings()

    return create_async_engine(
        settings.text2sql_database_url,
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=2,
    )


async def close_text2sql_engine():
    engine = get_text2sql_engine()
    await engine.dispose()
    get_text2sql_engine.cache_clear()


def normalize_value(value: Any,) -> Any:
    """
    将 PostgreSQL 返回的数据转换成
    后续 JSON / Tool 可以安全处理的类型。
    """

    if isinstance(
        value,
        Decimal,
    ):
        return float(value)

    if isinstance(
        value,
        (date, datetime),
    ):
        return value.isoformat()

    if isinstance(
        value,
        UUID,
    ):
        return str(value)

    return value


async def execute_readonly_sql(
    sql: str,
    max_rows: int | None = None,
) -> SQLExecutionResult:
    """
    安全执行一条 Text-to-SQL 查询。

    安全策略：

    1. Executor 内部再次执行 SQL Validator。
    2. 使用独立只读 PostgreSQL 用户。
    3. Transaction 强制 READ ONLY。
    4. 设置 statement_timeout。
    5. 外层强制 LIMIT。
    6. 最多返回指定数量的数据。
    """

    # =====================================================
    # 1. Executor 自己重新校验
    #
    # 即使上层已经 validate_sql()，
    # Executor 也不能相信调用方。
    # =====================================================

    validation = validate_sql(
        sql
    )

    if not validation.is_valid:
        raise SQLExecutionRejectedError(
            "SQL 未通过安全校验："
            + "; ".join(
                validation.errors
            )
        )

    if not validation.normalized_sql:
        raise SQLExecutionRejectedError(
            "SQL 标准化结果为空"
        )

    settings = get_settings()

    # =====================================================
    # 2. 限制最大返回行数
    # =====================================================

    configured_max_rows = (
        settings.text2sql_max_rows
    )

    if max_rows is None:
        safe_max_rows = (
            configured_max_rows
        )
    else:
        safe_max_rows = min(
            max_rows,
            configured_max_rows,
        )

    if safe_max_rows < 1:
        raise ValueError(
            "max_rows 必须大于 0"
        )

    # 多取一条，用于判断是否发生截断。
    database_limit = (
        safe_max_rows + 1
    )

    normalized_sql = (
        validation.normalized_sql
        .strip()
        .rstrip(";")
    )

    # =====================================================
    # 3. 再套一层 LIMIT
    #
    # 即使 LLM 生成：
    #
    # SELECT ...
    # FROM sales_records
    #
    # 没有 LIMIT，
    # Executor 最终也只允许有限数据返回。
    # =====================================================

    executable_sql = (
        "SELECT * "
        "FROM ("
        f"{normalized_sql}"
        ") AS __text2sql_result "
        f"LIMIT {database_limit}"
    )

    # =====================================================
    # 4. 查询超时
    # =====================================================

    timeout_ms = (
        settings
        .text2sql_statement_timeout_ms
    )

    # 再做一次程序层限制。
    timeout_ms = max(
        100,
        min(
            timeout_ms,
            30_000,
        ),
    )

    engine = get_text2sql_engine()

    try:
        async with engine.connect() as connection:

            async with connection.begin():

                # -----------------------------------------
                # 数据库事务级只读
                #
                # 即使数据库用户配置被误改，
                # 当前事务仍再次强制 READ ONLY。
                # -----------------------------------------

                await connection.exec_driver_sql(
                    "SET TRANSACTION READ ONLY"
                )

                # -----------------------------------------
                # 查询超时
                # -----------------------------------------

                await connection.exec_driver_sql(
                    (
                        "SET LOCAL statement_timeout "
                        f"= '{timeout_ms}ms'"
                    )
                )

                # -----------------------------------------
                # 真正执行 SQL
                # -----------------------------------------

                result = (
                    await connection.exec_driver_sql(
                        executable_sql
                    )
                )

                if not result.returns_rows:
                    raise SQLExecutionError(
                        "Text-to-SQL 只允许返回查询结果"
                    )

                columns = list(
                    result.keys()
                )

                raw_rows = (
                    result
                    .mappings()
                    .fetchmany(
                        database_limit
                    )
                )

    except SQLExecutionError:
        raise

    except DBAPIError as exc:
        error_message = str(
            exc
        ).lower()

        if (
            "statement timeout"
            in error_message
            or
            "canceling statement"
            in error_message
        ):
            raise SQLExecutionError(
                "SQL 查询超过允许的最大执行时间"
            ) from exc

        raise SQLExecutionError(
            "SQL 数据库执行失败"
        ) from exc

    # =====================================================
    # 5. 判断返回结果是否被截断
    # =====================================================

    truncated = (
        len(raw_rows)
        > safe_max_rows
    )

    raw_rows = raw_rows[
        :safe_max_rows
    ]

    # =====================================================
    # 6. JSON Friendly
    # =====================================================

    rows: list[
        dict[str, Any]
    ] = []

    for row in raw_rows:

        normalized_row = {
            key: normalize_value(
                value
            )
            for key, value
            in row.items()
        }

        rows.append(
            normalized_row
        )

    return SQLExecutionResult(
        sql=normalized_sql,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
    )