from typing import Literal

from pydantic import BaseModel, Field


class GraphChatRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        max_length=100,
        description="会话ID，相同thread_id共享对话记忆",
    )

    message: str = Field(
        min_length=1,
        max_length=2000,
        description="用户消息",
    )


class GraphChatResponse(BaseModel):
    thread_id: str
    answer: str

    route: Literal[
        "knowledge",
        "chat",
    ]

    route_reason: str

    used_tools: list[str]