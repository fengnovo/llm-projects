from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any

from app.database import get_db
from app.character.engine import ChatEngine
from app.character.persona import CHARACTERS


router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: str
    character_id: str
    message: str


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    emotion_state: Dict[str, float]
    tool_calls: list = []
    memory_summarized: bool = False


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    发送消息（非流式）
    
    - **session_id**: 会话ID，同一个会话保持连续对话
    - **character_id**: 角色ID，可选值：senior_sister（学姐）、tsundere（青梅竹马）
    - **message**: 用户消息
    """
    try:
        engine = ChatEngine(req.session_id, req.character_id, db)
        result = await engine.chat(req.message)
        return ChatResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务错误: {str(e)}")


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    流式聊天（SSE）
    """
    try:
        engine = ChatEngine(req.session_id, req.character_id, db)

        async def event_generator():
            async for chunk in engine.chat_stream(req.message):
                # 用 SSE 格式返回
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/characters")
async def list_characters():
    """获取可用角色列表"""
    return {
        "characters": [
            {
                "id": char.id,
                "name": char.name,
                "avatar": char.avatar,
                "description": char.description,
                "personality": char.personality,
            }
            for char in CHARACTERS.values()
        ]
    }
