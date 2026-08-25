import asyncio

from app.agents.sales_agent import (
    create_sales_agent,
)
from app.db import engine


async def main() -> None:
    query = (
        "按地区统计销售额，哪个地区最高？"
    )

    agent = create_sales_agent()

    try:
        print(
            "\n调用 Agent 前："
        )
        print(
            engine.sync_engine.pool.status()
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

        print(
            "\nAgent 执行完成后："
        )
        print(
            engine.sync_engine.pool.status()
        )

    finally:
        print(
            "\n准备 dispose："
        )
        print(
            engine.sync_engine.pool.status()
        )

        await engine.dispose()

        print(
            "\ndispose 完成："
        )
        print(
            engine.sync_engine.pool.status()
        )


if __name__ == "__main__":
    asyncio.run(main())