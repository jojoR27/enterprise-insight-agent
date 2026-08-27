from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Document,
    DocumentChunk,
)
from app.rag.embedding_service import get_embedding_service
from app.rag.text_splitter import split_text
from app.repositories.document_repository import DocumentRepository
from app.schemas.knowledge import (
    KnowledgeAskResponse,
    KnowledgeSearchItem,
    KnowledgeSearchResponse, KnowledgeCitation,
)
from app.rag.retrievers.pgvector_retriever import PgVectorRetriever

from app.services.llm_service import get_llm_service

import re

def validate_citations(answer: str,citations: list[KnowledgeCitation]) -> None:
    no_answer_text = ("根据当前知识库资料无法确定。")

    if answer.strip() == no_answer_text:
        return

    cited_numbers = re.findall(r"\[来源(\d+)\]",answer)
    if not cited_numbers:
        raise RuntimeError(
            "LLM 返回了答案，但没有提供引用"
        )

    valid_citations = {
        citation.citation
        for citation in citations
    }

    for number in cited_numbers:
        citation_name = f"来源{number}"

        if citation_name not in valid_citations:
            raise RuntimeError(
                f"LLM 返回了不存在的引用："
                f"[{citation_name}]"
            )


class RagService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = DocumentRepository(db)

        self.embedding_service = (
            get_embedding_service()
        )

    async def ingest_text(
        self,
        filename: str,
        text: str,
    ) -> Document:
        chunks = split_text(
            text=text,
            chunk_size=500,
            overlap=100,
        )

        if not chunks:
            raise ValueError("文档内容不能为空")

        embeddings = self.embedding_service.embed_documents(chunks)

        if len(chunks) != len(embeddings):
            raise RuntimeError("Chunk 数量与 Embedding 数量不一致")

        # 动态识别后缀，设置content_type
        suffix = filename.lower().split(".")[-1]
        content_type_map = {
            "txt": "text/plain",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        content_type = content_type_map.get(suffix, "application/octet-stream")

        document = Document(filename=filename, content_type=content_type)

        try:
            self.repository.add_document(document)
            await self.db.flush()
            chunk_models: list[DocumentChunk] = []
            for index, (content, embedding) in enumerate(
                zip(chunks, embeddings)
            ):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=content,
                    embedding=embedding,
                )
                chunk_models.append(chunk)

            self.repository.add_chunks(chunk_models)

            await self.db.commit()
            await self.db.refresh(document)

            return document

        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def search(
            self,
            query: str,
            limit: int = 3,
            min_similarity: float = 0.6,
    ) -> KnowledgeSearchResponse:
        retriever = PgVectorRetriever(
            repository=self.repository,
            embedding_service=self.embedding_service,
            k=limit,
            min_similarity=min_similarity,
        )

        documents = await retriever.ainvoke(query)

        results: list[KnowledgeSearchItem] = []

        for document in documents:
            metadata = document.metadata

            results.append(
                KnowledgeSearchItem(
                    chunk_id=metadata["chunk_id"],
                    document_id=metadata["document_id"],
                    filename=metadata["filename"],
                    chunk_index=metadata["chunk_index"],
                    content=document.page_content,
                    distance=metadata["distance"],
                    similarity=metadata["similarity"],
                )
            )

        return KnowledgeSearchResponse(
            query=query,
            count=len(results),
            results=results,
        )

    async def ask(
            self,
            query: str,
            limit: int = 3,
            min_similarity: float = 0.6,
    ) -> KnowledgeAskResponse:
        search_result = await self.search(
            query=query,
            limit=limit,
            min_similarity=min_similarity,
        )

        if not search_result.results:
            return KnowledgeAskResponse(
                query=query,
                answer="根据当前知识库资料无法确定。",
                sources=[],
            )

        context_parts: list[str] = []
        citations: list[KnowledgeCitation] = []

        for index, item in enumerate(
                search_result.results,
                start=1,
        ):
            citation = f"来源{index}"

            context_parts.append(
                (
                    f"[{citation}]\n"
                    f"文件：{item.filename}\n"
                    f"document_id：{item.document_id}\n"
                    f"chunk_id：{item.chunk_id}\n"
                    f"chunk_index：{item.chunk_index}\n"
                    f"内容：\n{item.content}"
                )
            )

            citations.append(
                KnowledgeCitation(
                    citation=citation,
                    filename=item.filename,
                    document_id=item.document_id,
                    chunk_id=item.chunk_id,
                    chunk_index=item.chunk_index,
                    similarity=item.similarity,
                    content=item.content,
                )
            )

        context = "\n\n".join(
            context_parts
        )

        llm_service = get_llm_service()

        answer = (
            await llm_service.answer_with_context(
                query=query,
                context=context,
            )
        )

        validate_citations(
            answer=answer,
            citations=citations,
        )

        return KnowledgeAskResponse(
            query=query,
            answer=answer,
            sources=citations,
        )