from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.sales import (
    SalesCreate,
    SalesResponse,
    SalesSummaryResponse,
)
from app.services.sales_service import SalesService


router = APIRouter()


@router.post(
    "/sales",
    response_model=SalesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sales_record(
    payload: SalesCreate,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = SalesService(db)

    try:
        return await service.create(payload)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="创建销售记录失败",
        )


@router.get(
    "/sales",
    response_model=list[SalesResponse],
)
async def get_sales_records(
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    region: str | None = None,
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    service = SalesService(db)

    return await service.list_records(
        region=region,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/sales/summary",
    response_model=list[SalesSummaryResponse],
)
async def get_sales_summary(
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = SalesService(db)

    return await service.summary()