import asyncio

from app.agents.knowledge_agent import (
    create_knowledge_agent,
)
from app.db import SessionLocal


async def main() -> None:
    query = "公司2026年总营业收入是多少？"

    async with SessionLocal() as db:
        agent = create_knowledge_agent(
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
            "\n========== Agent执行过程 ==========\n"
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