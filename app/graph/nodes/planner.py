from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)
from langgraph.types import (
    Overwrite,
    Send,
)

from app.graph.state import EnterpriseGraphState
from app.planner.planner import plan_request

def format_planner_conversation(state: EnterpriseGraphState,limit: int = 8) -> str:
    """
    给Planner最近几轮对话。
    Planner 需要结合上下文理解：
    “刚才的问题”
    “继续”
    “那销售额呢”
    等省略式请求。
    """
    lines: list[str] = []

    for message in state["messages"][-limit:]:
        if isinstance(message,HumanMessage):
            lines.append(f"用户：{message.content}")

        elif isinstance(message, AIMessage) and message.content:
            lines.append(f"助手：{message.content}")

    return "\n".join(lines)


async def planner_node(state: EnterpriseGraphState,) -> dict:
    """
    动态 Multi-Agent Graph 的调度入口。
    """
    conversation = (format_planner_conversation(state))

    if not conversation:
        raise RuntimeError("Planner 未找到有效对话内容")

    planner_input = (
        "下面是最近的对话历史。\n"
        "请重点处理最后一条用户消息，"
        "如果最后一条消息存在省略信息，"
        "请结合上下文理解。\n\n"
        f"{conversation}"
    )

    decision = await plan_request(planner_input)

    if decision is None:
        raise RuntimeError("Planner 返回空 Decision")

    tasks = [
        {
            "target": task.target,
            "instruction":task.instruction,
        }
        for task in decision.tasks
    ]

    return {
        "planner_mode":decision.mode,
        "planner_targets":decision.targets,
        "planner_tasks":tasks,
        "planner_reason":decision.reason,
        # 初始化容器
        "worker_results":Overwrite(value=[]),
        "used_tools": [],
    }


def dispatch_after_planner(state: EnterpriseGraphState):
    """
    根据 Planner 动态创建 Worker。
    Planner有几个task，
    就创建几个 Worker。
    """
    mode = state.get("planner_mode")
    if mode == "chat":
        return "chat"

    tasks = state.get("planner_tasks",[])

    if not tasks:
        raise RuntimeError("Planner 非 chat 模式但没有生成任何任务")

    return [
        Send("worker",{"task": task,})
        for task in tasks
    ]