from typing import Optional

from pydantic import BaseModel, Field

class KnowledgeCitation(BaseModel):
    citation: str
    filename: str
    document_id: int
    chunk_id: int
    chunk_index: int
    similarity: float
    content: str

# Swagger传进来的请求
class KnowledgeSearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
        description="需要检索的自然语言问题",
    )

    limit: int = Field(
        default=3,
        ge=1,
        le=20,
        description="返回最相关的 Chunk 数量",
    )

    min_similarity: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="最低相似度阈值",
    )


# 每一个检索到的 Chunk
class KnowledgeSearchItem(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    distance: float
    similarity: float
    filename: str


# 整个接口最终返回的数据
class KnowledgeSearchResponse(BaseModel):
    query: str
    count: int
    results: list[KnowledgeSearchItem]

# api输入规范
class KnowledgeAskRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
    )

    limit: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    min_similarity: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="最低相似度阈值",
    )

# api输出规范
class KnowledgeAskResponse(BaseModel):
    query: str
    answer: str
    sources: list[KnowledgeCitation]


class KnowledgeIngestResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[int] = None
    file_name: Optional[str] = None
