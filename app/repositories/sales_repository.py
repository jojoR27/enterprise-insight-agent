
from datetime import date
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

    # 条件过滤+聚合统计查询数据库
    async def analytics(
            self,
            region: str | None = None,
            product_name: str | None = None,
            channel: str | None = None,
            start_date: date | None = None,
            end_date: date | None = None,
            group_by: str = "none",
            limit: int = 20,
    ):
        filters = []

        if region:
            filters.append(
                SalesRecord.region == region
            )

        if product_name:
            filters.append(
                SalesRecord.product_name.ilike(
                    f"%{product_name}%"
                )
            )

        if channel:
            filters.append(
                SalesRecord.channel == channel
            )

        if start_date:
            filters.append(
                SalesRecord.sale_date >= start_date
            )

        if end_date:
            filters.append(
                SalesRecord.sale_date <= end_date
            )

        metrics = [
            func.count(
                SalesRecord.id
            ).label(
                "record_count"
            ),

            func.coalesce(
                func.sum(
                    SalesRecord.quantity
                ),
                0,
            ).label(
                "total_quantity"
            ),

            func.coalesce(
                func.sum(
                    SalesRecord.revenue
                ),
                0,
            ).label(
                "total_revenue"
            ),

            func.coalesce(
                func.avg(
                    SalesRecord.unit_price
                ),
                0,
            ).label(
                "avg_unit_price"
            ),
        ]

        group_columns = {
            "region": SalesRecord.region,
            "product": SalesRecord.product_name,
            "channel": SalesRecord.channel,
            "date": SalesRecord.sale_date,
        }

        if group_by == "none":
            statement = select(
                *metrics
            )

        else:
            group_column = group_columns.get(
                group_by
            )

            if group_column is None:
                raise ValueError(
                    f"不支持的 group_by：{group_by}"
                )

            statement = (
                select(
                    group_column.label(
                        "group_value"
                    ),
                    *metrics,
                )
                .group_by(
                    group_column
                )
                .order_by(
                    func.sum(
                        SalesRecord.revenue
                    ).desc()
                )
                .limit(limit)
            )

        if filters:
            statement = statement.where(
                *filters
            )

        result = await self.db.execute(
            statement
        )

        try:
            rows = result.mappings().all()
            return rows
        finally:
            result.close()