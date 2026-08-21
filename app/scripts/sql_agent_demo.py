import asyncio

from app.agents.sales_agent import (
    create_sales_agent,
)
from app.db import SessionLocal


async def main() -> None:
    query = (
        "按地区统计销售额，"
        "告诉我哪个地区销售额最高。"
    )

    async with SessionLocal() as db:
        agent = create_sales_agent(
            db
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": query,
                    }
                ]
            }
        )

        print(
            "\n========== Agent过程 ==========\n"
        )

        for message in result["messages"]:
            message.pretty_print()

        print(
            "\n========== 最终答案 ==========\n"
        )

        print(
            result["messages"][-1].content
        )


if __name__ == "__main__":
    asyncio.run(main())