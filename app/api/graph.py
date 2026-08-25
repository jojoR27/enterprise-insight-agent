
from fastapi import (
    APIRouter,
    Request,
)
from app.schemas.graph import (
    GraphChatRequest,
    GraphChatResponse,
)
from app.services.graph_service import (
    GraphService,
)


router = APIRouter()


@router.post(
    "/graph/chat",
    response_model=GraphChatResponse,
)
async def graph_chat(
    payload: GraphChatRequest,
    request: Request,
):
    graph = (
        request.app.state.enterprise_graph
    )

    service = GraphService(
        graph=graph,
    )

    return await service.chat(
        thread_id=payload.thread_id,
        message=payload.message,
    )