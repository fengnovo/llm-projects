from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.rag import router as rag_router


app = FastAPI(
    title="RAG 知识库问答系统",
    description="基于 ChromaDB + LangChain 的 RAG 知识库问答系统",
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

# 路由
app.include_router(rag_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "RAG 服务运行中"}


# 同源托管前端页面：访问 http://localhost:8001/ 直接打开界面，
# 页面与 API 同域，彻底避免跨域（mount 放在最后，不覆盖 /api、/docs、/health）
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
