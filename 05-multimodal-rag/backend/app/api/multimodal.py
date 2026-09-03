import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from app.config import settings
from app.multimodal_engine import get_multimodal_engine


router = APIRouter(prefix="/api/multimodal", tags=["multimodal"])


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    category: Optional[str] = None


class SearchResponse(BaseModel):
    results: list
    total: int


@router.post("/upload")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    上传图片到多模态内容库
    
    支持 jpg、png、webp 等常见格式，可一次上传多张
    """
    try:
        engine = get_multimodal_engine()

        file_data = []
        for file in files:
            content = await file.read()
            file_data.append((content, file.filename))

        result = engine.upload_images_batch(file_data)

        return {
            "success": True,
            **result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/search/text", response_model=SearchResponse)
async def search_by_text(req: SearchRequest):
    """
    文本搜图
    
    输入文字描述，返回最相关的图片
    """
    try:
        engine = get_multimodal_engine()
        results = engine.search_by_text(req.query, top_k=req.top_k, category=req.category)
        return SearchResponse(results=results, total=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/image")
async def search_by_image(file: UploadFile = File(...), top_k: int = 8):
    """
    以图搜图
    
    上传一张图片，找相似的图片
    """
    try:
        engine = get_multimodal_engine()
        content = await file.read()
        results = engine.search_by_image(content, top_k=top_k)
        return {"results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_for_chat(
    message: str = Form(...),
    context: Optional[str] = Form(None),
    top_k: int = 4,
):
    """
    对话内容推荐
    
    针对对话场景，根据用户消息推荐相关图片
    """
    try:
        engine = get_multimodal_engine()
        result = engine.recommend_for_chat(message, context or "", top_k=top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{filename}")
async def get_image(filename: str):
    """获取图片文件（静态文件服务）"""
    image_path = os.path.join(settings.IMAGE_DIR, filename)

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(image_path)


@router.get("/stats")
async def get_stats():
    """获取内容库统计"""
    try:
        engine = get_multimodal_engine()
        return engine.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_library():
    """清空内容库（谨慎使用）"""
    try:
        engine = get_multimodal_engine()
        engine.clear_all()
        return {"success": True, "message": "内容库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
