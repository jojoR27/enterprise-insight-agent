import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db import SessionLocal
from app.database.models import SalesRecord


async def insert_sales_record() -> None:
    async with SessionLocal() as session:
        record = SalesRecord(
            sale_date=date(2026, 8, 20),
            region="华东",
            product_name="企业AI知识库",
            channel="直销",
            quantity=2,
            unit_price=Decimal("999.00"),
            revenue=Decimal("1998.00"),
        )

        # 把数据提供给操作台 还未插入到数据表中
        session.add(record)
        # 真正把数据插入到数据表中
        await session.commit()
        await session.refresh(record)

        print("插入成功：")
        print(f"id = {record.id}")
        print(f"product_name = {record.product_name}")
        print(f"revenue = {record.revenue}")
        print(f"created_at = {record.created_at}")


async def query_sales_records() -> None:
    async with SessionLocal() as session:
        statement = (
            select(SalesRecord)
            .order_by(SalesRecord.id.desc())
        )

        result = await session.execute(statement)

        records = result.scalars().all()

        print("\n查询结果：")

        for record in records:
            print(
                record.id,
                record.sale_date,
                record.region,
                record.product_name,
                record.quantity,
                record.revenue,
            )


async def main() -> None:
    await insert_sales_record()
    await query_sales_records()


if __name__ == "__main__":
    asyncio.run(main())