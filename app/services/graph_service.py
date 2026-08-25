import logging

from app.graph.state import EnterpriseGraphContext
from app.observability.trace import AgentTrace
from app.schemas.graph import GraphChatResponse

logger = logging.getLogger("uvicorn.error")

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
        trace = AgentTrace(
            thread_id=thread_id,
        )
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        try:
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
                    trace=trace,
                ),
            )

            final_message = (
                result["messages"][-1]
            )

            return GraphChatResponse(
                thread_id=thread_id,
                trace_id=trace.trace_id,
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

        finally:
            trace.finish()

            logger.info(
                "agent_trace=%s",
                trace.model_dump_json(),
            )