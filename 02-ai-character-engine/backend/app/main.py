from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api.chat import router as chat_router
from app.api.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    yield


app = FastAPI(
    title="AI 角色聊天引擎",
    description="基于 FastAPI 的 AI 虚拟角色对话系统，支持记忆、情绪、Function Calling",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（前端开发用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)
app.include_router(sessions_router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "AI 角色引擎运行中"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
