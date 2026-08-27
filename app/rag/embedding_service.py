from functools import lru_cache

from sentence_transformers import SentenceTransformer
from app.config import get_settings


class EmbeddingService:
    def __init__(self):
        settings = get_settings()

        # 加载BGE Embedding模型  文本转语义向量模型
        self.model = SentenceTransformer(settings.embedding_model)

    # 输入：文本列表->512维语义向量/列表 列表   文档入库
    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    # 输入：用户问题->一个512维向量    用户搜索
    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )
        return embedding.tolist()

# 模型启动后预加载，只加载一次
@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()