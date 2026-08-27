from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
)
from app.services.agent_service import AgentService


router = APIRouter()

@router.post("/agent/chat",response_model=AgentChatResponse,)
async def agent_chat(
    payload: AgentChatRequest,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = AgentService(db)
    return await service.chat(payload.message)