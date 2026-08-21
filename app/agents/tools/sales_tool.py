# 接收大模型输出的查询参数，调用repository执行数据库统计,最后把查询结果以JSON字符串返回给大模型

import json
from datetime import date, datetime
from decimal import Decimal

from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sales_repository import (
    SalesRepository,
)
from app.schemas.sales_tool import (
    SalesQueryInput,
)


def normalize_value(value):
    if isinstance(
        value,
        Decimal,
    ):
        return float(value)

    if isinstance(
        value,
        (date, datetime),
    ):
        return value.isoformat()

    return value


def create_sales_tool(
    db: AsyncSession,
):
    repository = SalesRepository(
        db
    )

    @tool(
        "query_sales_data",
        args_schema=SalesQueryInput,
    )
    async def query_sales_data(
        region: str | None = None,
        product_name: str | None = None,
        channel: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        group_by: str = "none",
        limit: int = 20,
    ) -> str:
        """
        查询企业销售业务数据。

        用于查询销售额、销量、平均单价、
        地区销售、产品销售、渠道销售、
        日期范围销售等经营数据。

        本工具只执行只读统计查询。
        """

        rows = await repository.analytics(
            region=region,
            product_name=product_name,
            channel=channel,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
            limit=limit,
        )

        normalized_rows = []

        for row in rows:
            normalized_rows.append(
                {
                    key: normalize_value(value)
                    for key, value
                    in row.items()
                }
            )

        result = {
            "filters": {
                "region": region,
                "product_name": product_name,
                "channel": channel,
                "start_date": (
                    start_date.isoformat()
                    if start_date
                    else None
                ),
                "end_date": (
                    end_date.isoformat()
                    if end_date
                    else None
                ),
            },
            "group_by": group_by,
            "rows": normalized_rows,
        }

        return json.dumps(
            result,
            ensure_ascii=False,
        )

    return query_sales_data