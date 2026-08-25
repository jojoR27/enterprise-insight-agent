import asyncio

from app.agents.tools.text2sql_tool import (
    create_text2sql_tool,
)


async def main():
    tool = create_text2sql_tool()

    result = await tool.ainvoke(
        {
            "question": (
                "统计每个渠道销售额"
                "占总销售额的比例，"
                "并按比例从高到低排列。"
            )
        }
    )

    print("========== Text-to-SQL Tool ==========")

    print(result)


if __name__ == "__main__":
    asyncio.run(
        main()
    )