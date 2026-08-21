from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Document,
    DocumentChunk,
)


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def add_document(
        self,
        document: Document,
    ) -> None:
        self.db.add(document)

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> None:
        self.db.add_all(chunks)

    # 计算向量距离 找距离最小最相似的向量
    async def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 5,
        min_similarity: float = 0.6,
    ):
        distance = (
            DocumentChunk.embedding
            .cosine_distance(query_embedding)
        )

        max_distance = 1.0 - min_similarity

        statement = (
            select(
                DocumentChunk,
                Document.filename,
                distance.label("distance"),
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                distance <= max_distance
            )
            .order_by(
                distance.asc()
            )
            .limit(limit)
        )

        result = await self.db.execute(statement)

        return result.all()