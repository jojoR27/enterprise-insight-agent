import asyncio

from langchain_core.tools import tool

from app.agents.model import get_agent_model


@tool
def get_employee_annual_leave() -> str:
    """查询公司员工的年假制度。"""
    return "符合条件的员工每年享有10天带薪年假。"


async def main() -> None:
    model = get_agent_model()

    model_with_tools = model.bind_tools(
        [get_employee_annual_leave]
    )

    response = await model_with_tools.ainvoke(
        "我们公司的员工一年有多少天年假？"
    )

    print("content:")
    print(response.content)

    print("\ntool_calls:")
    print(response.tool_calls)


if __name__ == "__main__":
    asyncio.run(main())