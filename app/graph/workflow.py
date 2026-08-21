# LangGraph的图构建

from langgraph.checkpoint.memory import (
    InMemorySaver,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from app.graph.nodes import (
    chat_node,
    knowledge_node,
)
from app.graph.router import (
    router_node,
    select_route,
)
from app.graph.state import (
    EnterpriseGraphContext,
    EnterpriseGraphState,
)


def build_enterprise_graph(
    checkpointer,
):
    builder = StateGraph(
        EnterpriseGraphState,
        context_schema=EnterpriseGraphContext,
    )

    builder.add_node(
        "router",
        router_node,
    )

    builder.add_node(
        "knowledge",
        knowledge_node,
    )

    builder.add_node(
        "chat",
        chat_node,
    )

    builder.add_edge(
        START,
        "router",
    )

    builder.add_conditional_edges(
        "router",
        select_route,
        {
            "knowledge": "knowledge",
            "chat": "chat",
        },
    )

    builder.add_edge(
        "knowledge",
        END,
    )

    builder.add_edge(
        "chat",
        END,
    )

    return builder.compile(
        checkpointer=checkpointer,
        name="enterprise_insight_graph",
    )


enterprise_graph = build_enterprise_graph(
    InMemorySaver()
)