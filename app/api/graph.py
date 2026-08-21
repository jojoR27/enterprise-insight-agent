from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
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
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    graph = (
        request.app.state.enterprise_graph
    )

    service = GraphService(
        db=db,
        graph=graph,
    )

    return await service.chat(
        thread_id=payload.thread_id,
        message=payload.message,
    )