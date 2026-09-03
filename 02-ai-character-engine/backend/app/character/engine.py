"""
对话引擎核心

整合：人设 + 记忆系统 + 情绪状态机 + Function Calling

流程：
1. 接收用户消息
2. 构建 Prompt（人设 + 情绪 + 长期记忆 + 短期记忆）
3. 调用 LLM（支持 Function Calling）
4. 如果有工具调用，执行工具，把结果返回给 LLM 再生成最终回复
5. 更新情绪状态
6. 保存消息
7. 检查是否需要总结长期记忆
8. 返回回复
"""
import json
from typing import List, Dict, AsyncGenerator, Optional
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import Message, Conversation, EmotionState
from app.character.persona import get_character, Character
from app.character.memory import MemorySystem
from app.character.emotion import (
    EmotionStateMachine,
    analyze_emotion_from_text,
    generate_emotion_prompt,
    EmotionUpdate,
)
from app.character.tools import TOOL_DEFINITIONS, execute_tool


client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
)


class ChatEngine:
    """角色对话引擎"""

    def __init__(self, session_id: str, character_id: str, db: AsyncSession):
        self.session_id = session_id
        self.db = db
        self.character = get_character(character_id)
        self.memory = MemorySystem(
            session_id=session_id,
            db=db,
            window_size=settings.SHORT_TERM_MEMORY_WINDOW,
            summary_interval=settings.LONG_TERM_SUMMARY_INTERVAL,
        )

    async def _ensure_conversation(self):
        """确保会话存在，不存在则创建"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.session_id == self.session_id)
        )
        conv = result.scalar_one_or_none()

        if not conv:
            conv = Conversation(
                session_id=self.session_id,
                character_id=self.character.id,
            )
            self.db.add(conv)

            # 初始化情绪状态
            emotion_state = EmotionState(
                session_id=self.session_id,
                **self.character.initial_emotions
            )
            self.db.add(emotion_state)

            await self.db.commit()

        return conv

    async def _get_emotion_state(self) -> Dict[str, float]:
        """获取当前情绪状态"""
        result = await self.db.execute(
            select(EmotionState).where(EmotionState.session_id == self.session_id)
        )
        state = result.scalar_one_or_none()

        if not state:
            return self.character.initial_emotions.copy()

        return {
            "happiness": state.happiness,
            "sadness": state.sadness,
            "anger": state.anger,
            "fear": state.fear,
            "love": state.love,
            "shyness": state.shyness,
            "affection": state.affection,
        }

    async def _update_emotion_state(self, delta: EmotionUpdate):
        """更新情绪状态"""
        result = await self.db.execute(
            select(EmotionState).where(EmotionState.session_id == self.session_id)
        )
        state = result.scalar_one_or_none()

        if not state:
            state = EmotionState(
                session_id=self.session_id,
                **self.character.initial_emotions
            )
            self.db.add(state)

        machine = EmotionStateMachine({
            "happiness": state.happiness,
            "sadness": state.sadness,
            "anger": state.anger,
            "fear": state.fear,
            "love": state.love,
            "shyness": state.shyness,
            "affection": state.affection,
        })
        machine.update(delta)

        new_state = machine.get_state()
        state.happiness = new_state["happiness"]
        state.sadness = new_state["sadness"]
        state.anger = new_state["anger"]
        state.fear = new_state["fear"]
        state.love = new_state["love"]
        state.shyness = new_state["shyness"]
        state.affection = new_state["affection"]

        await self.db.commit()

    async def _build_system_prompt(self, emotion_state: Dict[str, float]) -> str:
        """构建完整的 System Prompt"""
        parts = [self.character.system_prompt.strip()]

        # 注入情绪状态
        emotion_prompt = generate_emotion_prompt(emotion_state)
        parts.append(emotion_prompt)

        # 注入长期记忆
        memory_prompt = await self.memory.build_memory_prompt()
        if memory_prompt:
            parts.append(memory_prompt)

        return "\n\n".join(parts)

    async def _save_message(self, role: str, content: str, metadata: dict = None):
        """保存一条消息"""
        msg = Message(
            session_id=self.session_id,
            role=role,
            content=content,
            metadata_=metadata or {},
        )
        self.db.add(msg)

        # 更新会话消息计数
        result = await self.db.execute(
            select(Conversation).where(Conversation.session_id == self.session_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            conv.message_count += 1

        await self.db.commit()

    async def chat(self, user_message: str) -> Dict:
        """
        完整对话流程（非流式）
        
        返回：
        {
            "reply": "AI 回复内容",
            "emotion_state": {...},
            "tool_calls": [...],
            "memory_summarized": bool,
        }
        """
        await self._ensure_conversation()

        # 保存用户消息
        await self._save_message("user", user_message)

        # 分析用户消息对情绪的影响
        emotion_delta = analyze_emotion_from_text(user_message, role="user")
        await self._update_emotion_state(emotion_delta)

        # 获取当前状态
        emotion_state = await self._get_emotion_state()
        short_term_memory = await self.memory.get_short_term_memory()

        # 构建消息列表
        system_prompt = await self._build_system_prompt(emotion_state)
        messages = [{"role": "system", "content": system_prompt}] + short_term_memory

        # 调用 LLM（带 Function Calling）
        reply, tool_calls = await self._call_llm_with_tools(messages)

        # 保存 AI 回复
        await self._save_message("assistant", reply, {"tool_calls": tool_calls})

        # 检查是否需要总结长期记忆
        memory_summarized = await self.memory.maybe_summarize()

        # 获取最新情绪状态
        emotion_state = await self._get_emotion_state()

        return {
            "reply": reply,
            "emotion_state": emotion_state,
            "tool_calls": tool_calls,
            "memory_summarized": memory_summarized,
        }

    async def chat_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        流式对话（简化版，不含 Function Calling 的流式处理）
        生产环境需要更复杂的流式工具调用处理
        """
        await self._ensure_conversation()

        # 保存用户消息
        await self._save_message("user", user_message)

        # 分析情绪
        emotion_delta = analyze_emotion_from_text(user_message, role="user")
        await self._update_emotion_state(emotion_delta)

        # 构建消息
        emotion_state = await self._get_emotion_state()
        short_term_memory = await self.memory.get_short_term_memory()
        system_prompt = await self._build_system_prompt(emotion_state)
        messages = [{"role": "system", "content": system_prompt}] + short_term_memory

        # 流式调用
        full_reply = ""
        try:
            stream = await client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=messages,
                stream=True,
                temperature=0.8,
                max_tokens=500,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_reply += content
                    yield content

        except Exception as e:
            yield f"\n\n[出错了：{str(e)}]"
            return

        # 保存 AI 回复
        await self._save_message("assistant", full_reply)

        # 检查总结（流式结束后异步触发，这里简化处理）
        await self.memory.maybe_summarize()

    async def _call_llm_with_tools(self, messages: List[Dict]) -> tuple[str, list]:
        """
        调用 LLM，支持 Function Calling
        
        流程：
        1. 第一次调用，看模型是否要调用工具
        2. 如果要调用，执行工具，把结果加回消息列表
        3. 第二次调用，让模型基于工具结果生成最终回复
        """
        tool_calls = []

        # 第一次调用（带工具定义）
        response = await client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.8,
            max_tokens=500,
        )

        response_message = response.choices[0].message

        # 如果没有工具调用，直接返回
        if not response_message.tool_calls:
            return response_message.content, []

        # 处理工具调用
        messages.append(response_message.model_dump())

        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            # 执行工具
            tool_result = await execute_tool(tool_name, tool_args)
            tool_calls.append({
                "name": tool_name,
                "args": tool_args,
                "result": tool_result,
            })

            # 把工具结果加回消息列表
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result, ensure_ascii=False),
            })

        # 第二次调用，让模型基于工具结果生成回复
        second_response = await client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=500,
        )

        return second_response.choices[0].message.content, tool_calls
