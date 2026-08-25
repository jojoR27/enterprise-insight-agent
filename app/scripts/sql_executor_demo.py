import asyncio

from app.text2sql.sql_executor import (
    close_text2sql_engine,
    execute_readonly_sql,
)
from app.text2sql.sql_generator import (
    generate_sql,
)
from app.text2sql.sql_validator import (
    validate_sql,
)


async def main():
    question = (
        "按时间统计销售额，"
        "哪一天最高？"
    )

    print("========== Question ==========")
    print(question)
    print()

    # ==========================================
    # 1. Natural Language → SQL
    # ==========================================

    generation = await generate_sql(question)

    print("========== Generated SQL ==========")
    print(generation.sql)
    print()
    print("========== Explanation ==========")
    print(generation.explanation)
    print()

    # ==========================================
    # 2. SQL Validator
    # ==========================================

    validation = validate_sql(generation.sql)

    print("========== Validation ==========")
    print(
        f"is_valid: "
        f"{validation.is_valid}"
    )

    print(
        f"errors: "
        f"{validation.errors}"
    )

    print()

    if not validation.is_valid:
        print(
            "SQL 未通过安全检查，"
            "终止执行。"
        )
        return

    # ==========================================
    # 3. Read-only Executor
    # ==========================================

    execution = await execute_readonly_sql(generation.sql)

    print("========== Execution ==========")

    print(
        f"columns: "
        f"{execution.columns}"
    )

    print(
        f"row_count: "
        f"{execution.row_count}"
    )

    print(
        f"truncated: "
        f"{execution.truncated}"
    )

    print()

    print("========== Rows ==========")

    for row in execution.rows:
        print(row)


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    finally:
        # Demo 进程结束时连接池会随进程释放。
        # FastAPI 生命周期接入后，
        # 我们会统一在 lifespan 中 dispose。
        pass