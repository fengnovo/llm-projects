from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models import Conversation, Message, EmotionState, LongTermMemory


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionInfo(BaseModel):
    session_id: str
    character_id: str
    message_count: int
    created_at: Optional[str] = None
    emotion_state: Optional[dict] = None


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取会话信息（包含情绪状态）"""
    result = await db.execute(
        select(Conversation).where(Conversation.session_id == session_id)
    )
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取情绪状态
    emotion_result = await db.execute(
        select(EmotionState).where(EmotionState.session_id == session_id)
    )
    emotion = emotion_result.scalar_one_or_none()

    return {
        "session_id": conv.session_id,
        "character_id": conv.character_id,
        "message_count": conv.message_count,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "emotion_state": {
            "happiness": emotion.happiness,
            "sadness": emotion.sadness,
            "anger": emotion.anger,
            "fear": emotion.fear,
            "love": emotion.love,
            "shyness": emotion.shyness,
            "affection": emotion.affection,
        } if emotion else None,
    }


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """获取会话历史消息"""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))

    return {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "metadata": msg.metadata_,
            }
            for msg in messages
        ]
    }


@router.get("/{session_id}/memories")
async def get_memories(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取长期记忆（事件簿）"""
    result = await db.execute(
        select(LongTermMemory)
        .where(LongTermMemory.session_id == session_id)
        .order_by(LongTermMemory.id.asc())
    )
    memories = result.scalars().all()

    return {
        "memories": [
            {
                "id": mem.id,
                "summary": mem.summary,
                "created_at": mem.created_at.isoformat() if mem.created_at else None,
            }
            for mem in memories
        ]
    }
