from pydantic import BaseModel, Field

# agent代码给llm的请求格式
class AgentChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )

# llm传给agent代码的回复格式
class AgentChatResponse(BaseModel):
    answer: str
    used_tools: list[str]