import asyncio

from app.db import SessionLocal
from app.rag.embedding_service import (
    get_embedding_service,
)
from app.rag.retrievers.pgvector_retriever import (
    PgVectorRetriever,
)
from app.repositories.document_repository import (
    DocumentRepository,
)


async def main() -> None:
    query = "员工一年可以休几天年假？"

    async with SessionLocal() as db:
        repository = DocumentRepository(db)

        retriever = PgVectorRetriever(
            repository=repository,
            embedding_service=get_embedding_service(),
            k=3,
            min_similarity=0.6,
        )

        documents = await retriever.ainvoke(
            query
        )

        print(f"问题：{query}")
        print(
            f"LangChain返回Document数量："
            f"{len(documents)}"
        )

        for index, document in enumerate(
            documents,
            start=1,
        ):
            print()
            print("=" * 60)
            print(f"排名：{index}")

            print(
                "filename：",
                document.metadata["filename"],
            )

            print(
                "chunk_id：",
                document.metadata["chunk_id"],
            )

            print(
                "similarity：",
                document.metadata["similarity"],
            )

            print("page_content：")
            print(document.page_content)


if __name__ == "__main__":
    asyncio.run(main())