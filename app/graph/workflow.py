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
)
from app.graph.planner_node import (
    dispatch_after_planner,
    planner_node,
)
from app.graph.result_nodes import (
    direct_result_node,
    result_coordinator_node,
    select_result_path,
    synthesis_node,
)
from app.graph.state import (
    EnterpriseGraphState,
)
from app.graph.worker import (
    worker_node,
)


def build_enterprise_graph(
    checkpointer,
):
    builder = StateGraph(
        EnterpriseGraphState,
    )

    # =========================
    # Nodes
    # =========================

    builder.add_node(
        "planner",
        planner_node,
    )

    builder.add_node(
        "worker",
        worker_node,
    )

    builder.add_node(
        "result_coordinator",
        result_coordinator_node,
    )

    builder.add_node(
        "direct_result",
        direct_result_node,
    )

    builder.add_node(
        "synthesis",
        synthesis_node,
    )

    builder.add_node(
        "chat",
        chat_node,
    )

    # =========================
    # Entry
    # =========================

    builder.add_edge(
        START,
        "planner",
    )

    # =========================
    # Planner
    #
    # chat:
    #   Planner → chat
    #
    # single / multi:
    #   Planner → Send(worker...)
    # =========================

    builder.add_conditional_edges(
        "planner",
        dispatch_after_planner,
    )

    # =========================
    # Worker 聚合
    # =========================

    builder.add_edge(
        "worker",
        "result_coordinator",
    )

    # =========================
    # Coordinator
    # =========================

    builder.add_conditional_edges(
        "result_coordinator",
        select_result_path,
        {
            "direct":
                "direct_result",

            "synthesis":
                "synthesis",
        },
    )

    # =========================
    # End
    # =========================

    builder.add_edge(
        "direct_result",
        END,
    )

    builder.add_edge(
        "synthesis",
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


enterprise_graph = (
    build_enterprise_graph(
        InMemorySaver()
    )
)