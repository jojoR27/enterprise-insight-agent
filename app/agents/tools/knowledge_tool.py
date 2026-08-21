from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_core.tools.retriever import (
    create_retriever_tool,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.embedding_service import (
    get_embedding_service,
)
from app.rag.retrievers.pgvector_retriever import (
    PgVectorRetriever,
)
from app.repositories.document_repository import (
    DocumentRepository,
)


def create_knowledge_tool(
    db: AsyncSession,
    k: int = 3,
    min_similarity: float = 0.6,
) -> BaseTool:
    repository = DocumentRepository(db)

    retriever = PgVectorRetriever(
        repository=repository,
        embedding_service=get_embedding_service(),
        k=k,
        min_similarity=min_similarity,
    )

    document_prompt = PromptTemplate.from_template(
        (
            "文件：{filename}\n"
            "document_id：{document_id}\n"
            "chunk_id：{chunk_id}\n"
            "chunk_index：{chunk_index}\n"
            "similarity：{similarity}\n"
            "内容：\n"
            "{page_content}"
        )
    )

    return create_retriever_tool(
        retriever=retriever,
        name="search_enterprise_knowledge",
        description=(
            "搜索企业内部知识库。"
            "当用户询问公司制度、员工手册、年假、"
            "考勤、报销、培训、信息安全、内部流程等"
            "企业内部知识时调用此工具。"
            "普通寒暄和常识问题不需要调用。"
        ),
        document_prompt=document_prompt,
        document_separator="\n\n---\n\n",
        response_format="content_and_artifact",
    )