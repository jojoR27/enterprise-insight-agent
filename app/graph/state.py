import operator
from typing import Literal, TypedDict, Annotated

from langgraph.graph import MessagesState
from typing_extensions import NotRequired

from app.planner.planner import (
    PlannerMode,
    PlannerTarget,
)

class WorkerTask(TypedDict):
    """
    Planner发给Worker的一个独立任务。
    """
    target: PlannerTarget
    instruction: str


class WorkerResult(TypedDict):
    """
    Worker执行完成后的标准结果。
    """
    target: PlannerTarget
    content: str
    used_tools: list[str]

ResultMode = Literal["direct","synthesis"]

class EnterpriseGraphState(MessagesState):
    """
        Enterprise Insight Agent
        整张 LangGraph 的共享状态。
    """
    planner_mode: NotRequired[PlannerMode]
    planner_targets: NotRequired[list[PlannerTarget]]
    planner_tasks: NotRequired[list[WorkerTask]]
    planner_reason: NotRequired[str]

    worker_results: Annotated[list[WorkerResult],operator.add]

    result_mode: NotRequired[ResultMode]
    used_tools: NotRequired[list[str]]