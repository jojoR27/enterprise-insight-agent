import asyncio

from app.observability.trace import AgentTrace


async def main():
    trace = AgentTrace(
        thread_id="trace-demo-001",
    )

    router_step = trace.start_step(
        name="router",
        category="router",
    )

    await asyncio.sleep(0.1)

    trace.finish_step(
        router_step,
        metadata={
            "route": "sql",
            "reason": "用户请求销售数据分析",
        },
    )

    tool_step = trace.start_step(
        name="text_to_sql",
        category="tool",
    )

    await asyncio.sleep(0.2)

    trace.finish_step(
        tool_step,
        metadata={
            "row_count": 3,
        },
    )

    trace.finish()

    print(
        trace.model_dump_json(
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())