from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SalesRecord
from app.repositories.sales_repository import SalesRepository
from app.schemas.sales import (
    SalesCreate,
    SalesSummaryResponse,
)


class SalesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SalesRepository(db)

    async def create(
        self,
        payload: SalesCreate,
    ) -> SalesRecord:
        revenue = (
            payload.unit_price
            * payload.quantity
        )

        record = SalesRecord(
            sale_date=payload.sale_date,
            region=payload.region,
            product_name=payload.product_name,
            channel=payload.channel,
            quantity=payload.quantity,
            unit_price=payload.unit_price,
            revenue=revenue,
        )

        try:
            await self.repository.add(record)

            await self.db.commit()

            await self.db.refresh(record)

            return record

        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def list_records(
        self,
        region: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SalesRecord]:
        return await self.repository.list(
            region=region,
            offset=offset,
            limit=limit,
        )

    async def summary(
        self,
    ) -> list[SalesSummaryResponse]:
        rows = await self.repository.summary_by_region()

        summaries = []

        for row in rows:
            summaries.append(
                SalesSummaryResponse(
                    region=row.region,
                    record_count=row.record_count,
                    total_quantity=row.total_quantity,
                    total_revenue=(
                        row.total_revenue
                        or Decimal("0")
                    ),
                )
            )

        return summaries