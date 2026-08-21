# DocumentChunk类对应数据库表 document_chunks，
# 一份原始/本地文档，会被代码切成很多小段chunk分块，每一个文本块，就是一条DocumentChunk数据库记录。
# DocumentChunk中document_id字段外键，用来指向documents.id=1，代表 “这个分块属于哪一份原始/本地文档”

from datetime import datetime

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 单个文本段转换为512维浮点数数组/向量的结果
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(512),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document = relationship(
        "Document",
        back_populates="chunks",
    )