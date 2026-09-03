"""
多模态内容推荐引擎

核心功能：
1. 图片上传 + 向量化 + 存储
2. 文本搜图（根据文字描述找相关图片）
3. 以图搜图（根据图片找相似图片）
4. 混合检索（文本 + 图像 + 标签）
5. 内容推荐（根据对话语境推荐相关图片）
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from PIL import Image
from app.config import settings
from app.embedder import get_embedder
from app.vector_db import get_vector_db


# 确保目录存在
os.makedirs(settings.IMAGE_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


class MultimodalEngine:
    """多模态内容推荐引擎"""

    def __init__(self):
        self.embedder = get_embedder()
        self.vector_db = get_vector_db()

    def upload_image(self, file_content: bytes, filename: str, metadata: dict = None) -> Dict[str, Any]:
        """
        上传图片并添加到向量库
        
        流程：
        1. 保存图片文件
        2. 生成缩略图
        3. CLIP 模型向量化
        4. 存入 Qdrant
        """
        # 保存文件
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']:
            ext = '.png'

        saved_path = os.path.join(settings.IMAGE_DIR, f"{file_id}{ext}")

        with open(saved_path, 'wb') as f:
            f.write(file_content)

        # 验证图片
        try:
            img = Image.open(saved_path)
            img.verify()
        except Exception as e:
            os.remove(saved_path)
            raise ValueError(f"无效的图片文件: {e}")

        # 向量化
        vector = self.embedder.encode_image(saved_path)

        # 存入向量库
        meta = metadata or {}
        meta["original_filename"] = filename
        point_id = self.vector_db.add_image(saved_path, vector, meta)

        return {
            "id": point_id,
            "path": saved_path,
            "filename": filename,
            "vector_size": len(vector),
            "metadata": meta,
        }

    def upload_images_batch(self, files: list) -> Dict[str, Any]:
        """批量上传图片"""
        items = []
        uploaded = []

        for file_content, filename in files:
            file_id = str(uuid.uuid4())
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                ext = '.png'

            saved_path = os.path.join(settings.IMAGE_DIR, f"{file_id}{ext}")

            with open(saved_path, 'wb') as f:
                f.write(file_content)

            try:
                vector = self.embedder.encode_image(saved_path)
                items.append({
                    "path": saved_path,
                    "vector": vector,
                    "metadata": {"original_filename": filename},
                })
                uploaded.append({"filename": filename, "path": saved_path})
            except Exception as e:
                os.remove(saved_path)
                uploaded.append({"filename": filename, "error": str(e)})

        if items:
            ids = self.vector_db.add_images_batch(items)
            for i, item in enumerate(items):
                if i < len(ids):
                    uploaded[i]["id"] = ids[i]

        return {
            "total": len(files),
            "success": len(items),
            "uploaded": uploaded,
        }

    def search_by_text(self, query: str, top_k: int = None, category: str = None) -> List[Dict]:
        """
        文本搜图
        
        输入一段文字描述，返回最相关的图片
        """
        top_k = top_k or settings.RETRIEVE_TOP_K

        # 文本向量化
        text_vector = self.embedder.encode_text(query)

        # 过滤条件
        filters = {}
        if category:
            filters["category"] = category

        # 搜索
        results = self.vector_db.search_by_text(text_vector, top_k=top_k, filters=filters)

        # 为结果添加可访问的 URL 路径（相对于静态文件服务）
        for result in results:
            path = result["payload"].get("path", "")
            result["payload"]["url"] = f"/images/{os.path.basename(path)}"

        return results

    def search_by_image(self, image_file: bytes, top_k: int = None) -> List[Dict]:
        """
        以图搜图
        
        上传一张图片，找相似的图片
        """
        top_k = top_k or settings.RETRIEVE_TOP_K

        # 保存临时文件
        temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.png")
        with open(temp_path, 'wb') as f:
            f.write(image_file)

        try:
            # 向量化
            image_vector = self.embedder.encode_image(temp_path)

            # 搜索
            results = self.vector_db.search_by_image(image_vector, top_k=top_k)

            # 添加 URL
            for result in results:
                path = result["payload"].get("path", "")
                result["payload"]["url"] = f"/images/{os.path.basename(path)}"

            return results
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def recommend_for_chat(self, user_message: str, context: str = "", top_k: int = 4) -> Dict[str, Any]:
        """
        针对对话场景的内容推荐
        
        结合用户当前消息和对话上下文，推荐相关的图片内容。
        这是对接 AI 角色引擎的接口，让角色聊天时能"发图"。
        """
        # 构建检索查询（结合上下文和当前消息）
        if context:
            query = f"{context}\n{user_message}"
        else:
            query = user_message

        # 文本搜图
        results = self.search_by_text(query, top_k=top_k)

        # 生成推荐理由（简化版，实际可以用 LLM 生成）
        recommendation = {
            "recommended": results[:top_k],
            "reason": f"根据你说的「{user_message[:30]}」，为你找到这些相关图片",
            "confidence": results[0]["score"] if results else 0,
        }

        return recommendation

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.vector_db.get_stats()

    def clear_all(self) -> bool:
        """清空所有内容"""
        # 清理图片文件
        import shutil
        if os.path.exists(settings.IMAGE_DIR):
            shutil.rmtree(settings.IMAGE_DIR)
            os.makedirs(settings.IMAGE_DIR)

        # 清理向量库
        self.vector_db.clear()
        return True


# 全局单例
_engine = None


def get_multimodal_engine() -> MultimodalEngine:
    global _engine
    if _engine is None:
        _engine = MultimodalEngine()
    return _engine
