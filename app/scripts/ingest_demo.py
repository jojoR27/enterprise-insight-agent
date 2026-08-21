import asyncio
from pathlib import Path

from app.db import SessionLocal
from app.services.rag_service import RagService


async def main() -> None:
    file_path = Path(
        "data/employee_handbook.txt"
    )

    text = file_path.read_text(encoding="utf-8")

    print(f"开始导入文档：{file_path.name}")

    print(f"文档字符数：{len(text)}")

    async with SessionLocal() as db:
        service = RagService(db)

        document = await service.ingest_text(
            filename=file_path.name,
            text=text,
        )

        print("文档入库成功")
        print(f"document_id = {document.id}")
        print(f"filename = {document.filename}")


if __name__ == "__main__":
    asyncio.run(main())