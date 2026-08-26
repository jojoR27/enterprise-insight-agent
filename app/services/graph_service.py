from app.schemas.graph import (
    GraphChatResponse,
)


class GraphService:
    def __init__(
        self,
        graph,
    ):
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
        )

        final_message = (
            result["messages"][-1]
        )

        return GraphChatResponse(
            thread_id=thread_id,

            answer=str(
                final_message.content
            ),

            mode=result[
                "planner_mode"
            ],

            targets=result.get(
                "planner_targets",
                [],
            ),

            planner_reason=result.get(
                "planner_reason",
                "",
            ),

            used_tools=result.get(
                "used_tools",
                [],
            ),
        )