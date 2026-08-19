from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import get_settings
from app.db import engine


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    # 程序关机的时候，把SQLAlchemy的数据库连接池清理掉。
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"],
)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "message": "Enterprise Insight Agent API is running.",
    }