from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.state import (
    EnterpriseGraphContext,
)
from app.schemas.graph import (
    GraphChatResponse,
)


class GraphService:
    def __init__(
        self,
        db: AsyncSession,
        graph,
    ):
        self.db = db
        self.graph = graph

    async def chat(
        self,
        thread_id: str,
        message: str,
    ) -> GraphChatResponse:
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        result = await self.graph.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
            },
            config=config,
            context=EnterpriseGraphContext(
                db=self.db
            ),
        )

        final_message = (
            result["messages"][-1]
        )

        return GraphChatResponse(
            thread_id=thread_id,
            answer=str(
                final_message.content
            ),
            route=result["route"],
            route_reason=result[
                "route_reason"
            ],
            used_tools=result.get(
                "used_tools",
                [],
            ),
        )