import asyncio

from app.db import SessionLocal
from app.services.rag_service import RagService


async def main() -> None:
    query = "员工一年可以休几天年假？"

    async with SessionLocal() as db:
        service = RagService(db)

        rows = await service.search(
            query=query,
            limit=3,
        )

        print(f"\n问题：{query}")
        print("=" * 60)

        for index, (chunk, distance) in enumerate(
            rows,
            start=1,
        ):
            similarity = 1 - float(distance)

            print(f"\n排名：{index}")
            print(f"chunk_id：{chunk.id}")
            print(
                f"document_id：{chunk.document_id}"
            )
            print(
                f"chunk_index：{chunk.chunk_index}"
            )
            print(
                f"distance：{float(distance):.4f}"
            )
            print(
                f"similarity：{similarity:.4f}"
            )
            print("内容：")
            print(chunk.content)
            print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())