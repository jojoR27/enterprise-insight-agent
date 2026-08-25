import asyncio

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

    generation = await generate_sql(question)

    print("========== Generated SQL ==========")

    print(generation.sql)

    print()

    validation = validate_sql(generation.sql)

    print("========== Validation ==========")

    print(f"is_valid: "f"{validation.is_valid}")

    print(f"errors: "f"{validation.errors}")

    print(f"warnings: "f"{validation.warnings}")

    print()

    print("========== Normalized SQL ==========")

    print(validation.normalized_sql)


if __name__ == "__main__":
    asyncio.run(
        main()
    )