import asyncio

from app.agents.tools.sales_tool import (
    create_sales_tool,
)
from app.db import SessionLocal


async def main() -> None:
    async with SessionLocal() as db:
        tool = create_sales_tool(
            db
        )

        result = await tool.ainvoke(
            {
                "group_by": "region",
                "limit": 20,
            }
        )

        print(
            "========== SQL Tool =========="
        )

        print(result)


if __name__ == "__main__":
    asyncio.run(main())