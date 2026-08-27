# 后续要补充一个api接口用于先传入的知识文本分割等操作后入库  √

from typing import Annotated

from app.core.file_parser import extract_text_from_file
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.knowledge import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeIngestResponse,
)
from app.services.rag_service import RagService


router = APIRouter()

# 这个接口对应rag_service的search方法 多余的
@router.post("/knowledge/search",response_model=KnowledgeSearchResponse)
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Annotated[AsyncSession,Depends(get_db),],
):
    service = RagService(db)

    return await service.search(
        query=payload.query,
        limit=payload.limit,
        min_similarity=payload.min_similarity,
    )


@router.post("/knowledge/ask",response_model=KnowledgeAskResponse)
async def ask_knowledge(
    payload: KnowledgeAskRequest,
    db: Annotated[AsyncSession,Depends(get_db),],
):
    service = RagService(db)

    return await service.ask(
        query=payload.query,
        limit=payload.limit,
        min_similarity=payload.min_similarity,
    )


# 新增  新文本入库操作接口
@router.post("/knowledge/ingest", response_model=KnowledgeIngestResponse)
async def ingest_knowledge(
    db: Annotated[AsyncSession,Depends(get_db),],
    file: UploadFile = File(...),
):
    service = RagService(db)
    filename = file.filename
    # 调用解析文件的自定义方法 针对不同类型的文件
    text = await extract_text_from_file(file)
    doc = await service.ingest_text(filename, text)

    return KnowledgeIngestResponse(
        success=True,
        message="文档入库成功",
        document_id=doc.id,
        file_name=filename
    )