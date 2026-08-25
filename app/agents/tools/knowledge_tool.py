from pydantic import BaseModel, Field
from langchain_core.tools import tool

from app.db import SessionLocal
from app.rag.embedding_service import (
    get_embedding_service,
)
from app.rag.retrievers.pgvector_retriever import (
    PgVectorRetriever,
)
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.observability.trace import AgentTrace


class KnowledgeToolInput(BaseModel):
    query: str = Field(description="需要在企业内部知识库中检索的问题")

def create_knowledge_tool(
    k: int = 3,
    min_similarity: float = 0.6,
    trace: AgentTrace | None = None,
):
    @tool(
        "search_enterprise_knowledge",
        args_schema=KnowledgeToolInput,
        response_format="content_and_artifact",
    )
    async def search_enterprise_knowledge(
        query: str,
    ):
        """
        搜索企业内部知识库。

        当用户询问公司制度、员工手册、年假、
        考勤、报销、培训、信息安全、内部流程等
        企业内部知识时使用。
        """
        step = None

        if trace is not None:
            step = trace.start_step(
                name="search_enterprise_knowledge",
                category="tool",
                metadata={
                    "query_length": len(query),
                    "k": k,
                    "min_similarity": min_similarity,
                },
            )

        try:
            async with SessionLocal() as db:
                repository = DocumentRepository(
                    db
                )

                retriever = PgVectorRetriever(
                    repository=repository,
                    embedding_service=(
                        get_embedding_service()
                    ),
                    k=k,
                    min_similarity=min_similarity,
                )

                documents = await retriever.ainvoke(
                    query
                )

            if not documents:
                return (
                    "当前企业知识库没有找到足够相关的资料。",
                    [],
                )

            content_parts: list[str] = []

            for index, document in enumerate(
                documents,
                start=1,
            ):
                metadata = document.metadata

                content_parts.append(
                    (
                        f"[资料{index}]\n"
                        f"文件：{metadata.get('filename')}\n"
                        f"document_id："
                        f"{metadata.get('document_id')}\n"
                        f"chunk_id："
                        f"{metadata.get('chunk_id')}\n"
                        f"chunk_index："
                        f"{metadata.get('chunk_index')}\n"
                        f"similarity："
                        f"{metadata.get('similarity')}\n"
                        f"内容：\n"
                        f"{document.page_content}"
                    )
                )

            content = "\n\n---\n\n".join(
                content_parts
            )

            if (
                    trace is not None
                    and step is not None
            ):
                trace.finish_step(
                    step,
                    metadata={
                        "result_count": len(
                            documents
                        ),
                    },
                )

            return (
                content,
                documents,
            )

        except Exception as exc:
            if (
                    trace is not None
                    and step is not None
                    and step.finished_at is None
            ):
                trace.finish_step(
                    step,
                    success=False,
                    error=str(exc),
                )

            raise

    return search_enterprise_knowledge