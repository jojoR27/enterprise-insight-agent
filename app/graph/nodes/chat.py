from langchain_core.messages import SystemMessage

from app.agents.model import get_agent_model
from app.graph.state import EnterpriseGraphState


async def chat_node(state: EnterpriseGraphState,) -> dict:
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
        "messages": [response],
        "used_tools": [],
    }