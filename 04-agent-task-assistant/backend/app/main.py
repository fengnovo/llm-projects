from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.agent import router as agent_router


app = FastAPI(
    title="Agent 任务助手",
    description="基于 LangGraph 的 ReAct Agent，支持多工具调用",
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
app.include_router(agent_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Agent 服务运行中"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
