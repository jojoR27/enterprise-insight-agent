# 给sql语句再做一层安全检查 阻止对数据库的CRUD操作

# 第三层
# SQL Validator
# → AST 强制检查

from pydantic import BaseModel, Field
from sqlglot import exp, parse
from sqlglot.errors import ParseError

from app.text2sql.schema_registry import (
    get_allowed_columns,
    get_allowed_tables,
)


class SQLValidationResult(BaseModel):
    is_valid: bool

    normalized_sql: str | None = None

    errors: list[str] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )

    referenced_tables: list[str] = Field(
        default_factory=list
    )

    referenced_columns: list[str] = Field(
        default_factory=list
    )


# 这些语法节点即使藏在 SELECT / CTE 里面，
# 也不允许出现。
DANGEROUS_NODE_TYPES = {
    "insert",
    "update",
    "delete",
    "drop",
    "create",
    "alter",
    "truncate",
    "truncatetable",
    "merge",
    "command",
    "copy",
    "grant",
    "revoke",
    "transaction",

    # PostgreSQL:
    # SELECT ... INTO new_table
    # 会创建新表，所以必须禁止。
    "into",

    # SELECT ... FOR UPDATE 等锁语句
    # 对真正只读分析场景也没有必要开放。
    "lock",
}


ALLOWED_SCHEMAS = {
    "public",
}


MAX_SQL_LENGTH = 10_000


def validate_sql(sql: str,) -> SQLValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    referenced_tables: set[str] = set()
    referenced_columns: set[str] = set()

    sql = sql.strip()

    if not sql:
        return SQLValidationResult(
            is_valid=False,
            errors=[
                "SQL 不能为空"
            ],
        )

    if len(sql) > MAX_SQL_LENGTH:
        return SQLValidationResult(
            is_valid=False,
            errors=[
                (
                    "SQL 长度超过允许限制："
                    f"{MAX_SQL_LENGTH}"
                )
            ],
        )

    try:
        statements = parse(
            sql,
            read="postgres",
        )
    except ParseError as exc:
        return SQLValidationResult(
            is_valid=False,
            errors=[
                f"SQL 语法解析失败：{exc}"
            ],
        )
    statements = [
        statement
        for statement in statements
        if statement is not None
    ]

    if len(statements) != 1:
        return SQLValidationResult(
            is_valid=False,
            errors=[
                (
                    "只允许执行一条 SQL 语句，"
                    f"当前检测到 {len(statements)} 条"
                )
            ],
        )
    statement = statements[0]

    if not isinstance(
        statement,
        exp.Query,
    ):
        errors.append(
            "只允许 SELECT / 查询类型 SQL"
        )

    # =====================================================
    # 5. AST 全树检查危险操作
    #
    # 不能只看最外层。
    #
    # 例如：
    #
    # WITH x AS (
    #     DELETE FROM ...
    # )
    # SELECT ...
    #
    # 外层看起来可能是 SELECT，
    # 但内部仍然存在 DELETE。
    # =====================================================

    for node in statement.walk():
        node_type = (
            node.__class__.__name__.lower()
        )

        if (
            node_type
            in DANGEROUS_NODE_TYPES
        ):
            errors.append(
                (
                    "检测到禁止的 SQL 操作："
                    f"{node.__class__.__name__}"
                )
            )

    # =====================================================
    # 6. 收集 CTE 名称
    #
    # WITH monthly_sales AS (...)
    #
    # monthly_sales 是临时查询结果，
    # 不是数据库真实表。
    # =====================================================

    cte_names: set[str] = set()

    for cte in statement.find_all(
        exp.CTE
    ):
        cte_name = cte.alias_or_name

        if cte_name:
            cte_names.add(
                cte_name.lower()
            )

    # =====================================================
    # 7. 收集子查询 Alias
    #
    # FROM (
    #     SELECT ...
    # ) AS monthly_sales
    #
    # monthly_sales 同样不是数据库真实表。
    # =====================================================

    derived_table_names: set[str] = set()

    for subquery in statement.find_all(
        exp.Subquery
    ):
        alias = subquery.alias_or_name

        if alias:
            derived_table_names.add(
                alias.lower()
            )

    # =====================================================
    # 8. 检查数据库真实表白名单
    # =====================================================

    allowed_tables = {
        table.lower()
        for table in get_allowed_tables()
    }

    table_alias_mapping: dict[
        str,
        str,
    ] = {}

    for table in statement.find_all(
        exp.Table
    ):
        table_name = table.name

        if not table_name:
            continue

        normalized_table = (
            table_name.lower()
        )

        # CTE 引用不是真实数据库表
        if normalized_table in cte_names:
            continue

        referenced_tables.add(
            normalized_table
        )

        if (
            normalized_table
            not in allowed_tables
        ):
            errors.append(
                (
                    "SQL 使用了未授权的数据表："
                    f"{table_name}"
                )
            )

        # -----------------------------------------
        # 限制 Schema
        #
        # sales_records
        # public.sales_records
        # 可以
        #
        # pg_catalog.xxx
        # 不允许
        # -----------------------------------------

        schema_name = table.db

        if schema_name:
            normalized_schema = str(
                schema_name
            ).lower()

            if (
                normalized_schema
                not in ALLOWED_SCHEMAS
            ):
                errors.append(
                    (
                        "SQL 使用了未授权的 Schema："
                        f"{schema_name}"
                    )
                )

        # -----------------------------------------
        # 建立表 Alias 映射
        #
        # FROM sales_records AS s
        #
        # s -> sales_records
        # -----------------------------------------

        alias = table.alias_or_name

        if alias:
            table_alias_mapping[
                alias.lower()
            ] = normalized_table

        table_alias_mapping[
            normalized_table
        ] = normalized_table

    # =====================================================
    # 9. SELECT *
    #
    # Text-to-SQL 默认禁止直接返回全部字段。
    #
    # 原因：
    # 1. 避免意外暴露未来新增字段
    # 2. 避免返回大量无关数据
    # 3. 强迫 Generator 明确选择业务字段
    #
    # COUNT(*) 不受这里影响。
    # =====================================================

    for select in statement.find_all(
        exp.Select
    ):
        for projection in (
            select.expressions
        ):
            if isinstance(
                projection,
                exp.Star,
            ):
                errors.append(
                    "禁止使用 SELECT *"
                )

            if (
                isinstance(
                    projection,
                    exp.Column,
                )
                and isinstance(
                    projection.this,
                    exp.Star,
                )
            ):
                errors.append(
                    "禁止使用 table.*"
                )

    # =====================================================
    # 10. 收集 SQL 中定义的别名
    #
    # SELECT SUM(revenue) AS total_revenue
    # ORDER BY total_revenue
    #
    # total_revenue 并不是数据库字段，
    # 所以不能误判为非法字段。
    # =====================================================

    expression_aliases: set[str] = set()

    for alias_expression in (
        statement.find_all(
            exp.Alias
        )
    ):
        alias_name = (
            alias_expression.alias
        )

        if alias_name:
            expression_aliases.add(
                alias_name.lower()
            )

    # =====================================================
    # 11. 字段白名单检查
    # =====================================================

    for column in statement.find_all(
        exp.Column
    ):
        column_name = column.name

        if not column_name:
            continue

        normalized_column = (
            column_name.lower()
        )

        # SELECT 别名，例如：
        #
        # ORDER BY total_revenue
        #
        # 不是真实字段。
        if (
            normalized_column
            in expression_aliases
        ):
            continue

        referenced_columns.add(
            normalized_column
        )

        qualifier = column.table

        # -----------------------------------------
        # 有明确表前缀：
        #
        # s.revenue
        # -----------------------------------------

        if qualifier:
            normalized_qualifier = (
                qualifier.lower()
            )

            # CTE / 派生表中的字段，
            # 由它内部的原始查询继续校验。
            if (
                normalized_qualifier
                in cte_names
                or normalized_qualifier
                in derived_table_names
            ):
                continue

            real_table = (
                table_alias_mapping.get(
                    normalized_qualifier
                )
            )

            if real_table is None:
                errors.append(
                    (
                        "字段引用了未知表或别名："
                        f"{qualifier}.{column_name}"
                    )
                )
                continue

            allowed_columns = {
                name.lower()
                for name
                in get_allowed_columns(
                    real_table
                )
            }

            if (
                normalized_column
                not in allowed_columns
            ):
                errors.append(
                    (
                        "SQL 使用了未授权字段："
                        f"{real_table}."
                        f"{column_name}"
                    )
                )

            continue

        # -----------------------------------------
        # 没有表前缀：
        #
        # SELECT revenue
        #
        # 当前只有一个真实表时，
        # 可以明确验证。
        # -----------------------------------------

        real_tables = {
            table
            for table
            in referenced_tables
            if table in allowed_tables
        }

        if len(real_tables) == 1:
            real_table = next(
                iter(real_tables)
            )

            allowed_columns = {
                name.lower()
                for name
                in get_allowed_columns(
                    real_table
                )
            }

            if (
                normalized_column
                not in allowed_columns
            ):
                errors.append(
                    (
                        "SQL 使用了未授权字段："
                        f"{real_table}."
                        f"{column_name}"
                    )
                )

        elif len(real_tables) == 0:
            # SELECT 1 等不访问业务表的查询。
            warnings.append(
                (
                    "检测到未绑定业务表的字段："
                    f"{column_name}"
                )
            )

        else:
            # 以后增加多个业务表后，
            # 无表前缀字段可能存在歧义。
            warnings.append(
                (
                    "字段未明确指定所属表："
                    f"{column_name}"
                )
            )

    # =====================================================
    # 12. 去重错误和警告
    # =====================================================

    errors = list(
        dict.fromkeys(
            errors
        )
    )

    warnings = list(
        dict.fromkeys(
            warnings
        )
    )

    # =====================================================
    # 13. SQL 标准化
    #
    # 注意：
    # 标准化 ≠ 安全。
    # 是否允许执行仍然由 is_valid 决定。
    # =====================================================

    normalized_sql: str | None = None

    try:
        normalized_sql = statement.sql(
            dialect="postgres",
            pretty=True,
        )
    except Exception:
        warnings.append(
            "SQL 标准化失败"
        )

    return SQLValidationResult(
        is_valid=not errors,
        normalized_sql=(
            normalized_sql
            if not errors
            else None
        ),
        errors=errors,
        warnings=warnings,
        referenced_tables=sorted(
            referenced_tables
        ),
        referenced_columns=sorted(
            referenced_columns
        ),
    )