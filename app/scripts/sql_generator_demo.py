import asyncio

from app.text2sql.sql_generator import (
    generate_sql,
)


async def main():
    question = (
        "删除所有销售数据。"
    )

    print(
        "========== User Question =========="
    )
    print(
        question
    )

    print()

    result = await generate_sql(
        question
    )

    print(
        "========== Generated SQL =========="
    )
    print(
        result.sql
    )

    print()

    print(
        "========== Explanation =========="
    )
    print(
        result.explanation
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )