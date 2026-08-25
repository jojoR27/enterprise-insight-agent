from dataclasses import dataclass
from app.observability.trace import AgentTrace
from typing import Literal

from langgraph.graph import MessagesState
from typing_extensions import NotRequired

# 路由可选值  二选一
RouteName = Literal[
    "knowledge",
    "sql",
    "hybrid",
    "chat",
]

# state工作台
class EnterpriseGraphState(MessagesState):
    route: NotRequired[RouteName]
    route_reason: NotRequired[str]
    used_tools: NotRequired[list[str]]

# Runtime Context：本次运行临时上下文，绝不持久化
@dataclass
class EnterpriseGraphContext:
    trace: AgentTrace