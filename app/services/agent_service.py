from langchain_core.messages import ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.knowledge_agent import (
    create_knowledge_agent,
)
from app.schemas.agent import AgentChatResponse


class AgentService:
    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def chat(
        self,
        message: str,
    ) -> AgentChatResponse:
        agent = create_knowledge_agent()

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
            }
        )

        used_tools: list[str] = []

        for item in result["messages"]:
            if isinstance(
                item,
                ToolMessage,
            ):
                if item.name:
                    used_tools.append(
                        item.name
                    )

        final_message = (
            result["messages"][-1]
        )

        return AgentChatResponse(
            answer=str(
                final_message.content
            ),
            used_tools=used_tools,
        )