"""
向量数据库封装

使用 ChromaDB，轻量级，本地文件持久化，不需要单独部署服务。
生产环境建议替换为 Milvus 或 Qdrant。
"""
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from app.config import settings


class VectorStore:
    """向量数据库管理"""

    def __init__(self):
        # 确保数据目录存在
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Embedding 模型
        # check_embedding_ctx_length=False：关闭 tiktoken 分词，直接发送字符串数组
        # （OpenAI 官方接受 token ID 数组，但阿里云 MaaS / DashScope 兼容端点只接受字符串数组）
        # chunk_size=10：兼容端点单次请求最多 10 条文本的限制
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
            check_embedding_ctx_length=False,
            chunk_size=10,
        )

        # LangChain Chroma 封装
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: list, metadatas: list = None, ids: list = None):
        """添加文档到向量库"""
        return self.vectorstore.add_texts(
            texts=documents,
            metadatas=metadatas or [{}] * len(documents),
            ids=ids,
        )

    def similarity_search(self, query: str, k: int = None) -> list:
        """相似度检索"""
        k = k or settings.RETRIEVE_TOP_K
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        # 返回文档内容、元数据、相似度分数
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]

    def get_collection_stats(self) -> dict:
        """获取集合统计信息"""
        collection = self.client.get_collection(settings.CHROMA_COLLECTION_NAME)
        count = collection.count()
        return {
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "document_count": count,
        }

    def delete_collection(self):
        """清空集合（谨慎使用）"""
        try:
            self.client.delete_collection(settings.CHROMA_COLLECTION_NAME)
            # 重新创建
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=settings.CHROMA_COLLECTION_NAME,
                embedding_function=self.embeddings,
            )
            return True
        except Exception as e:
            print(f"删除集合失败: {e}")
            return False


# 全局单例
_vector_store = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
