import asyncio
import sys

from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)

from app.config import get_settings

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

async def main() -> None:
    settings = get_settings()

    async with AsyncPostgresSaver.from_conn_string(
        settings.langgraph_database_url
    ) as checkpointer:
        await checkpointer.setup()

    print(
        "LangGraph PostgreSQL Memory "
        "初始化完成"
    )


if __name__ == "__main__":
    asyncio.run(main())