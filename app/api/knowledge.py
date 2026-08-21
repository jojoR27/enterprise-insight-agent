from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.knowledge import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services.rag_service import RagService


router = APIRouter()


@router.post(
    "/knowledge/search",
    response_model=KnowledgeSearchResponse,
)
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = RagService(db)

    return await service.search(
        query=payload.query,
        limit=payload.limit,
        min_similarity=payload.min_similarity,
    )


@router.post(
    "/knowledge/ask",
    response_model=KnowledgeAskResponse,
)
async def ask_knowledge(
    payload: KnowledgeAskRequest,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = RagService(db)

    return await service.ask(
        query=payload.query,
        limit=payload.limit,
        min_similarity=payload.min_similarity,
    )