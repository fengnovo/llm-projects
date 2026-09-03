import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.multimodal import router as multimodal_router


app = FastAPI(
    title="多模态内容推荐系统",
    description="基于 CLIP + Qdrant 的多模态图文检索与内容推荐系统",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（图片）
os.makedirs(settings.IMAGE_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=settings.IMAGE_DIR), name="images")

# 路由
app.include_router(multimodal_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "多模态服务运行中"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
