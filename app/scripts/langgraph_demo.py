import asyncio

from app.db import SessionLocal
from app.graph.state import (
    EnterpriseGraphContext,
)
from app.graph.workflow import (
    enterprise_graph,
)


async def main() -> None:
    thread_id = "demo-001"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    async with SessionLocal() as db:
        context = EnterpriseGraphContext(
            db=db
        )

        questions = [
            "员工一年可以休几天年假？",
            "那申请需要提前几天？",
            "我刚才主要在问什么？",
        ]

        for question in questions:
            print()
            print("=" * 70)
            print(
                f"用户：{question}"
            )

            result = (
                await enterprise_graph.ainvoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": question,
                            }
                        ]
                    },
                    config=config,
                    context=context,
                )
            )

            print(
                "Route：",
                result.get("route"),
            )

            print(
                "Route Reason：",
                result.get("route_reason"),
            )

            print(
                "Used Tools：",
                result.get("used_tools"),
            )

            print(
                "Answer：",
                result["messages"][-1].content,
            )


if __name__ == "__main__":
    asyncio.run(main())