# 数据库表长什么样

from app.database.models.document import Document
from app.database.models.document_chunk import DocumentChunk
from app.database.models.sales_record import SalesRecord

__all__ = [
    "Document",
    "DocumentChunk",
    "SalesRecord",
]