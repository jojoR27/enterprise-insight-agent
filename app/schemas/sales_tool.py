from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class SalesQueryInput(BaseModel):
    region: str | None = Field(
        default=None,
        description=(
            "地区筛选，例如：华东、华北。"
            "不需要地区筛选时为空。"
        ),
    )

    product_name: str | None = Field(
        default=None,
        description=(
            "产品名称筛选，支持产品名称关键词。"
        ),
    )

    channel: str | None = Field(
        default=None,
        description=(
            "销售渠道筛选。"
        ),
    )

    start_date: date | None = Field(
        default=None,
        description=(
            "开始日期，格式 YYYY-MM-DD。"
        ),
    )

    end_date: date | None = Field(
        default=None,
        description=(
            "结束日期，格式 YYYY-MM-DD。"
        ),
    )

    group_by: Literal[
        "none",
        "region",
        "product",
        "channel",
        "date",
    ] = Field(
        default="none",
        description=(
            "统计维度。"
            "none表示整体汇总；"
            "region按地区；"
            "product按产品；"
            "channel按渠道；"
            "date按日期。"
        ),
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="最多返回多少组数据",
    )