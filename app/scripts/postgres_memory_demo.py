import asyncio
import sys

from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)

from app.config import get_settings
from app.db import SessionLocal
from app.graph.state import (
    EnterpriseGraphContext,
)
from app.graph.workflow import (
    build_enterprise_graph,
)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


async def main() -> None:
    settings = get_settings()

    thread_id = "postgres-memory-test-001"

    message = input("用户：").strip()

    if not message:
        print("请输入问题")
        return

    async with AsyncPostgresSaver.from_conn_string(
        settings.langgraph_database_url
    ) as checkpointer:

        graph = build_enterprise_graph(
            checkpointer
        )

        async with SessionLocal() as db:
            context = EnterpriseGraphContext(
                db=db
            )

            result = await graph.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message,
                        }
                    ]
                },
                config={
                    "configurable": {
                        "thread_id": thread_id,
                    }
                },
                context=context,
            )

            print()
            print("=" * 70)

            print(
                "Thread ID：",
                thread_id,
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
                result.get("used_tools", []),
            )

            print(
                "Answer：",
                result["messages"][-1].content,
            )


if __name__ == "__main__":
    asyncio.run(main())