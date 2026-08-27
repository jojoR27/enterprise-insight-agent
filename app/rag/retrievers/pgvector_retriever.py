import asyncio

from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from app.rag.embedding_service import EmbeddingService
from app.repositories.document_repository import DocumentRepository


class PgVectorRetriever(BaseRetriever):
    repository: DocumentRepository
    embedding_service: EmbeddingService

    k: int = 3
    min_similarity: float = 0.6

    model_config = ConfigDict(arbitrary_types_allowed=True,)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        raise NotImplementedError("当前 Retriever 使用异步数据库连接，请使用 await retriever.ainvoke(query)")

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> list[Document]:
        # 输入问题向量化
        query_embedding = await asyncio.to_thread(
            self.embedding_service.embed_query,
            query,
        )

        rows = await self.repository.search_similar(
            query_embedding=query_embedding,
            limit=self.k,
            min_similarity=self.min_similarity,
        )

        documents: list[Document] = []

        for chunk, filename, distance in rows:
            distance_value = float(distance)
            similarity = 1.0 - distance_value

            document = Document(
                page_content=chunk.content,
                metadata={
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": filename,
                    "chunk_index": chunk.chunk_index,
                    "distance": distance_value,
                    "similarity": similarity,
                },
            )

            documents.append(document)

        return documents