"""
向量数据库封装 - Qdrant

Qdrant 是一个高性能的向量数据库，支持：
- 本地模式（不需要单独部署服务）
- 服务模式（生产环境）
- 多种索引类型
- 过滤检索
"""
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.config import settings


class VectorDB:
    """Qdrant 向量数据库"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 确保目录存在
        os.makedirs(settings.QDRANT_PATH, exist_ok=True)

        # 使用本地模式
        self.client = QdrantClient(path=settings.QDRANT_PATH)

        # 确保集合存在
        self._ensure_collection()

    def _ensure_collection(self):
        """确保集合存在，不存在则创建"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if settings.QDRANT_COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=settings.QDRANT_VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            print(f"创建集合: {settings.QDRANT_COLLECTION}")

    def add_image(self, image_path: str, vector: list, metadata: dict = None) -> str:
        """添加一张图片到向量库"""
        point_id = str(uuid.uuid4())

        payload = {
            "type": "image",
            "path": image_path,
            "filename": os.path.basename(image_path),
        }
        if metadata:
            payload.update(metadata)

        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        return point_id

    def add_images_batch(self, items: list) -> list:
        """
        批量添加图片
        
        items: [{"path": "...", "vector": [...], "metadata": {...}}, ...]
        """
        points = []
        for item in items:
            point_id = str(uuid.uuid4())
            payload = {
                "type": "image",
                "path": item["path"],
                "filename": os.path.basename(item["path"]),
            }
            if item.get("metadata"):
                payload.update(item["metadata"])

            points.append(PointStruct(
                id=point_id,
                vector=item["vector"],
                payload=payload,
            ))

        if points:
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=points,
            )

        return [p.id for p in points]

    def search_by_text(self, text_vector: list, top_k: int = None, filters: dict = None) -> list:
        """
        用文本向量搜索图片
        
        返回：[{"id", "score", "payload"}, ...]
        """
        top_k = top_k or settings.RETRIEVE_TOP_K

        search_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(FieldCondition(
                    key=key,
                    match=MatchValue(value=value),
                ))
            search_filter = Filter(must=conditions)

        response = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=text_vector,
            limit=top_k,
            query_filter=search_filter,
        )
        results = response.points

        return [
            {
                "id": hit.id,
                "score": float(hit.score),
                "payload": hit.payload,
            }
            for hit in results
        ]

    def search_by_image(self, image_vector: list, top_k: int = None) -> list:
        """用图像向量搜索相似图片（以图搜图）"""
        top_k = top_k or settings.RETRIEVE_TOP_K

        response = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=image_vector,
            limit=top_k,
        )
        results = response.points

        return [
            {
                "id": hit.id,
                "score": float(hit.score),
                "payload": hit.payload,
            }
            for hit in results
        ]

    def hybrid_search(
        self,
        text_vector: list,
        image_vector: list = None,
        text_weight: float = None,
        image_weight: float = None,
        top_k: int = None,
    ) -> list:
        """
        混合检索：文本 + 图像向量加权融合
        
        原理：分别用文本和图像检索，然后按权重融合分数
        """
        top_k = top_k or settings.RETRIEVE_TOP_K
        text_weight = text_weight if text_weight is not None else settings.TEXT_WEIGHT
        image_weight = image_weight if image_weight is not None else settings.IMAGE_WEIGHT

        # 文本检索
        text_results = self.search_by_text(text_vector, top_k=top_k * 2)

        if image_vector is None:
            # 只有文本，直接返回
            return text_results[:top_k]

        # 图像检索
        image_results = self.search_by_image(image_vector, top_k=top_k * 2)

        # 融合结果（RRF 算法简化版：按排名加权）
        score_map = {}

        for rank, item in enumerate(text_results):
            score_map[item["id"]] = {
                "item": item,
                "text_rank": rank,
                "image_rank": 9999,
            }

        for rank, item in enumerate(image_results):
            if item["id"] in score_map:
                score_map[item["id"]]["image_rank"] = rank
            else:
                score_map[item["id"]] = {
                    "item": item,
                    "text_rank": 9999,
                    "image_rank": rank,
                }

        # 计算融合分数（RRF：倒数排名融合）
        def rrf_score(entry):
            k = 60  # RRF 常数
            text_score = 1 / (k + entry["text_rank"]) * text_weight
            image_score = 1 / (k + entry["image_rank"]) * image_weight
            return text_score + image_score

        fused = sorted(
            score_map.values(),
            key=rrf_score,
            reverse=True,
        )

        # 返回 top_k
        return [
            {
                "id": entry["item"]["id"],
                "score": rrf_score(entry),
                "payload": entry["item"]["payload"],
                "text_rank": entry["text_rank"],
                "image_rank": entry["image_rank"],
            }
            for entry in fused[:top_k]
        ]

    def get_stats(self) -> dict:
        """获取集合统计"""
        info = self.client.get_collection(settings.QDRANT_COLLECTION)
        return {
            "collection_name": settings.QDRANT_COLLECTION,
            "points_count": info.points_count,
            "vectors_count": getattr(info, "indexed_vectors_count", info.points_count),
            "status": str(info.status),
        }

    def clear(self):
        """清空集合"""
        self.client.delete_collection(settings.QDRANT_COLLECTION)
        self._ensure_collection()
        return True


def get_vector_db() -> VectorDB:
    """获取全局单例"""
    return VectorDB()
