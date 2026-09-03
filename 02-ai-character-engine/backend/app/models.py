from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.sql import func
from app.database import Base


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, comment="会话ID")
    character_id = Column(String(64), index=True, comment="角色ID")
    user_id = Column(String(64), index=True, default="default", comment="用户ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    message_count = Column(Integer, default=0, comment="消息总数")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True)
    role = Column(String(16), comment="user / assistant / system")
    content = Column(Text, comment="消息内容")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_ = Column("metadata", JSON, default={}, comment="元数据（情绪、工具调用等）")


class LongTermMemory(Base):
    """长期记忆表（事件簿）"""
    __tablename__ = "long_term_memories"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True)
    summary = Column(Text, comment="总结内容")
    start_message_id = Column(Integer, comment="起始消息ID")
    end_message_id = Column(Integer, comment="结束消息ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tags = Column(JSON, default=[], comment="标签（用于检索）")


class EmotionState(Base):
    """情绪状态表"""
    __tablename__ = "emotion_states"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True)
    # 多维情绪数值（0-100）
    happiness = Column(Float, default=50.0, comment="开心")
    sadness = Column(Float, default=10.0, comment="悲伤")
    anger = Column(Float, default=5.0, comment="生气")
    fear = Column(Float, default=5.0, comment="害怕")
    love = Column(Float, default=30.0, comment="爱慕")
    shyness = Column(Float, default=20.0, comment="害羞")
    # 好感度（0-100）
    affection = Column(Float, default=20.0, comment="好感度")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
