import operator
from dataclasses import dataclass

from app.observability.trace import AgentTrace
from typing import Literal, TypedDict, Annotated

from langgraph.graph import MessagesState
from typing_extensions import NotRequired
from app.planner.planner import (
    PlannerMode,
    PlannerTarget,
)

# 路由可选值  多选一
RouteName = Literal[
    "knowledge",
    "sql",
    "hybrid",
    "chat",
]

class WorkerTask(TypedDict):
    """
    Planner 发给 Worker 的一个独立任务。
    """
    target: PlannerTarget
    instruction: str


class WorkerResult(TypedDict):
    """
    一个 Worker 执行完成后的标准结果。
    """
    target: PlannerTarget
    content: str
    used_tools: list[str]

ResultMode = Literal[
    "direct",
    "synthesis",
]

# state工作台
class EnterpriseGraphState(MessagesState):
    result_mode: NotRequired[ResultMode]
    used_tools: NotRequired[list[str]]

    planner_mode: NotRequired[
        PlannerMode
    ]

    planner_targets: NotRequired[
        list[PlannerTarget]
    ]

    planner_tasks: NotRequired[
        dict[str, str]
    ]

    planner_reason: NotRequired[str]

    worker_results: Annotated[
        list[WorkerResult],
        operator.add,
    ]

# Runtime Context：本次运行临时上下文，绝不持久化
@dataclass
class EnterpriseGraphContext:
    trace: AgentTrace