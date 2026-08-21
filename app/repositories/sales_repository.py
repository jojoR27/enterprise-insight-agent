from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SalesRecord


class SalesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        record: SalesRecord,
    ) -> SalesRecord:
        self.db.add(record)
        return record

    async def list_records(
        self,
        region: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SalesRecord]:
        statement = (
            select(SalesRecord)
            .order_by(SalesRecord.id.desc())
            .offset(offset)
            .limit(limit)
        )

        if region:
            statement = statement.where(
                SalesRecord.region == region
            )

        result = await self.db.execute(statement)

        return list(result.scalars().all())

    async def summary_by_region(self):
        statement = (
            select(
                SalesRecord.region,
                func.count(SalesRecord.id).label(
                    "record_count"
                ),
                func.sum(SalesRecord.quantity).label(
                    "total_quantity"
                ),
                func.sum(SalesRecord.revenue).label(
                    "total_revenue"
                ),
            )
            .group_by(SalesRecord.region)
            .order_by(
                func.sum(SalesRecord.revenue).desc()
            )
        )

        result = await self.db.execute(statement)

        return result.all()