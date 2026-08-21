# knowledge_node是知识库业务节点   chat_node是普通闲聊节点

from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.runtime import Runtime

from app.agents.knowledge_agent import (
    create_knowledge_agent,
)
from app.agents.sales_agent import (
    create_sales_agent,
)
from app.agents.model import get_agent_model
from app.graph.state import (
    EnterpriseGraphContext,
    EnterpriseGraphState,
)


async def knowledge_node(
    state: EnterpriseGraphState,
    runtime: Runtime[
        EnterpriseGraphContext
    ],
) -> dict:
    agent = create_knowledge_agent(
        runtime.context.db
    )

    result = await agent.ainvoke(
        {
            "messages": state["messages"]
        }
    )

    used_tools: list[str] = []

    for message in result["messages"]:
        if (
            isinstance(message, ToolMessage)
            and message.name
            and message.name not in used_tools
        ):
            used_tools.append(
                message.name
            )

    final_message = result["messages"][-1]

    if not isinstance(
        final_message,
        AIMessage,
    ):
        raise RuntimeError(
            "Knowledge Agent 未返回最终 AIMessage"
        )

    return {
        "messages": [
            final_message
        ],
        "used_tools": used_tools,
    }


async def chat_node(
    state: EnterpriseGraphState,
) -> dict:
    model = get_agent_model()

    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    "你是 Enterprise Insight Agent。"
                    "当前节点负责普通对话。"
                    "请结合已有聊天历史自然回答。"
                )
            ),
            *state["messages"],
        ]
    )

    return {
        "messages": [
            response
        ],
        "used_tools": [],
    }


async def sql_node(
    state: EnterpriseGraphState,
    runtime: Runtime[
        EnterpriseGraphContext
    ],
) -> dict:
    agent = create_sales_agent(
        runtime.context.db
    )

    result = await agent.ainvoke(
        {
            "messages": state["messages"]
        }
    )

    used_tools: list[str] = []

    for message in result["messages"]:
        if (
            isinstance(
                message,
                ToolMessage,
            )
            and message.name
            and message.name
            not in used_tools
        ):
            used_tools.append(
                message.name
            )

    final_message = (
        result["messages"][-1]
    )

    if not isinstance(
        final_message,
        AIMessage,
    ):
        raise RuntimeError(
            "Sales Agent 未返回最终 AIMessage"
        )

    return {
        "messages": [
            final_message
        ],
        "used_tools": used_tools,
    }