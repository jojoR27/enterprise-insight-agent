from contextlib import asynccontextmanager

from fastapi import FastAPI

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.graph.persistence import create_langgraph_pool
from app.graph.workflow import build_enterprise_graph
from app.api.health import router as health_router
from app.api.sales import router as sales_router
from app.api.knowledge import router as knowledge_router
from app.api.agent import router as agent_router
from app.api.graph import router as graph_router
from app.config import get_settings
from app.db import engine



settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    langgraph_pool = create_langgraph_pool()
    await langgraph_pool.open(wait=True)
    checkpointer = AsyncPostgresSaver(langgraph_pool)

    app.state.enterprise_graph = build_enterprise_graph(checkpointer)
    app.state.langgraph_pool = langgraph_pool

    try:
        yield

    finally:
        await langgraph_pool.close()
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

app.include_router(
    sales_router,
    prefix="/api/v1",
    tags=["Sales"],
)

app.include_router(
    knowledge_router,
    prefix="/api/v1",
    tags=["Knowledge"],
)

app.include_router(
    agent_router,
    prefix="/api/v1",
    tags=["Agent"],
)

app.include_router(
    graph_router,
    prefix="/api/v1",
    tags=["LangGraph"],
)

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "message": "Enterprise Insight Agent API is running.",
    }