import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db import check_database


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    try:
        pgvector_version = await check_database()

        return {
            "status": "ok",
            "database": "ok",
            "pgvector": (
                pgvector_version
                if pgvector_version
                else "not_enabled"
            ),
        }

    except Exception:
        logger.exception("Database health check failed")

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "database": "down",
                "pgvector": "unknown",
            },
        )