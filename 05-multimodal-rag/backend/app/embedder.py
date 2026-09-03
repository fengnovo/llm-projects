"""
多模态 Embedding 模型封装

使用 CLIP 模型同时支持：
- 文本 → 向量
- 图像 → 向量

两者在同一个向量空间，可以互相检索。
"""
import os
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from app.config import settings


class MultimodalEmbedder:
    """多模态 Embedding 模型"""

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

        # 设备选择
        if settings.DEVICE == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = settings.DEVICE

        print(f"使用设备: {self.device}")
        print(f"加载 CLIP 模型: {settings.CLIP_MODEL_NAME}")

        # 加载 CLIP 模型（图文统一向量空间）
        self.clip_model = SentenceTransformer(
            settings.CLIP_MODEL_NAME,
            device=self.device,
        )

        # 向量维度
        self.vector_size = self.clip_model.get_sentence_embedding_dimension()
        print(f"向量维度: {self.vector_size}")

    def encode_text(self, text: str) -> list:
        """文本 → 向量"""
        embedding = self.clip_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def encode_texts(self, texts: list) -> list:
        """批量文本 → 向量"""
        embeddings = self.clip_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def encode_image(self, image_path: str) -> list:
        """图像 → 向量"""
        from sentence_transformers import SentenceTransformer

        # CLIP 的图像编码
        # sentence-transformers 2.x 的 CLIP 模型支持图像输入
        img = Image.open(image_path).convert("RGB")
        embedding = self.clip_model.encode(
            img,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def encode_images(self, image_paths: list) -> list:
        """批量图像 → 向量"""
        images = [Image.open(p).convert("RGB") for p in image_paths]
        embeddings = self.clip_model.encode(
            images,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def similarity(self, text: str, image_path: str) -> float:
        """计算图文相似度"""
        text_emb = self.encode_text(text)
        img_emb = self.encode_image(image_path)
        # 余弦相似度（已归一化，直接点积）
        return sum(a * b for a, b in zip(text_emb, img_emb))


def get_embedder() -> MultimodalEmbedder:
    """获取全局单例"""
    return MultimodalEmbedder()
