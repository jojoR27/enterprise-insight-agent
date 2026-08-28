from collections.abc import (
    Awaitable,
    Callable,
)

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from typing_extensions import TypedDict

from app.agents.knowledge_agent import create_knowledge_agent
from app.agents.sales_agent import create_sales_agent
from app.graph.state import (
    PlannerTarget,
    WorkerResult,
    WorkerTask,
)


class WorkerState(TypedDict):
    """
    Send给单个Worker的局部状态。后续可能有字段扩展 所以单独再封装一个类
    """
    task: WorkerTask

def collect_used_tools(messages) -> list[str]:
    used_tools: list[str] = []

    for message in messages:
        if (isinstance(message,ToolMessage,) and message.name and message.name not in used_tools):
            used_tools.append(message.name)

    return used_tools


# 后面增加agent同时也要增加对应方法
async def run_knowledge_worker(instruction: str) -> WorkerResult:
    agent = create_knowledge_agent()

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content=instruction)]
        }
    )

    final_message = result["messages"][-1]

    if not isinstance(final_message,AIMessage,):
        raise RuntimeError("Knowledge Agent 未返回最终 AIMessage")

    return {
        "target": "knowledge",
        "content": str(final_message.content),
        "used_tools":collect_used_tools(result["messages"]),
    }


async def run_sales_worker(instruction: str,) -> WorkerResult:
    agent = create_sales_agent()

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content=instruction)]
        }
    )

    final_message = result["messages"][-1]

    if not isinstance(final_message,AIMessage,):
        raise RuntimeError("Sales Agent未返回最终 AIMessage")

    return {
        "target": "sales",
        "content": str(final_message.content),
        "used_tools":collect_used_tools(result["messages"]),
    }


WorkerHandler = Callable[[str],Awaitable[WorkerResult]]

WORKER_REGISTRY: dict[PlannerTarget,WorkerHandler] = {
    "knowledge":run_knowledge_worker,
    "sales":run_sales_worker,
}

async def worker_node(state: WorkerState) -> dict:
    """
    通用 Worker Node。
    Planner 决定谁做；
    Registry 找到对应 Worker；
    Worker 再调用专业 Agent。
    """
    task = state["task"]
    target = task["target"]
    instruction = (task["instruction"])

    handler = WORKER_REGISTRY.get(target)

    if handler is None:
        raise RuntimeError(f"未注册 Worker: {target}")

    result = await handler(instruction)

    return {"worker_results": [result]}