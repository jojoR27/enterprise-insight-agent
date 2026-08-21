# 给LLM的输入数据格式规范

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# post请求 用户创建销售记录时的请求格式
class SalesCreate(BaseModel):
    sale_date: date

    region: str = Field(
        min_length=1,
        max_length=100,
    )

    product_name: str = Field(
        min_length=1,
        max_length=200,
    )

    channel: str = Field(
        min_length=1,
        max_length=50,
    )

    quantity: int = Field(
        gt=0,
    )

    unit_price: Decimal = Field(
        gt=0,
        decimal_places=2,
    )

# api返回的单条数据格式 单条销售数据响应格式
class SalesResponse(BaseModel):
    id: int
    sale_date: date
    region: str
    product_name: str
    channel: str
    quantity: int
    unit_price: Decimal
    revenue: Decimal
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

# api返回聚合统计响应格式
class SalesSummaryResponse(BaseModel):
    region: str
    record_count: int
    total_quantity: int
    total_revenue: Decimal