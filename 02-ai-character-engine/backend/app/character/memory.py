"""
记忆系统

包含：
1. 短期记忆：最近 N 轮对话（滑动窗口）
2. 长期记忆：基于"事件簿"的自动总结机制

原理：
- 每次对话后，如果消息数达到阈值，就触发一次总结
- 总结结果作为"事件"存入长期记忆
- 下次对话时，从长期记忆中检索相关事件，注入到 Prompt 中
- 这样即使对话很长，也不会丢失关键信息
"""
from typing import List, Dict
from openai import AsyncOpenAI
from app.config import settings
from app.models import Message, LongTermMemory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
)


class MemorySystem:
    """记忆系统"""

    def __init__(self, session_id: str, db: AsyncSession, window_size: int = 20, summary_interval: int = 10):
        self.session_id = session_id
        self.db = db
        self.window_size = window_size
        self.summary_interval = summary_interval

    async def get_short_term_memory(self) -> List[Dict[str, str]]:
        """获取短期记忆（最近 N 轮对话）"""
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == self.session_id)
            .order_by(Message.id.desc())
            .limit(self.window_size)
        )
        messages = list(reversed(result.scalars().all()))
        return [{"role": m.role, "content": m.content} for m in messages]

    async def get_long_term_memory(self) -> str:
        """获取长期记忆（事件簿总结）"""
        result = await self.db.execute(
            select(LongTermMemory)
            .where(LongTermMemory.session_id == self.session_id)
            .order_by(LongTermMemory.id.asc())
        )
        memories = result.scalars().all()

        if not memories:
            return ""

        # 简单拼接所有总结（生产环境可以做向量检索，只召回相关的）
        parts = []
        for i, mem in enumerate(memories, 1):
            parts.append(f"事件 {i}：{mem.summary}")

        return "\n".join(parts)

    async def maybe_summarize(self) -> bool:
        """
        检查是否需要总结，如果需要则生成总结并存入长期记忆
        返回是否触发了总结
        """
        # 统计当前消息数
        result = await self.db.execute(
            select(Message).where(Message.session_id == self.session_id)
        )
        total = len(result.scalars().all())

        # 获取最后一次总结的结束消息ID
        last_summary_result = await self.db.execute(
            select(LongTermMemory)
            .where(LongTermMemory.session_id == self.session_id)
            .order_by(LongTermMemory.id.desc())
            .limit(1)
        )
        last_summary = last_summary_result.scalar_one_or_none()

        last_end_id = last_summary.end_message_id if last_summary else 0

        # 如果从上一次总结后又积累了足够的消息，触发新的总结
        new_messages_count = total - last_end_id
        if new_messages_count < self.summary_interval:
            return False

        # 获取需要总结的消息
        result = await self.db.execute(
            select(Message)
            .where(
                Message.session_id == self.session_id,
                Message.id > last_end_id,
                Message.role.in_(["user", "assistant"])
            )
            .order_by(Message.id.asc())
        )
        messages_to_summarize = result.scalars().all()

        if len(messages_to_summarize) < self.summary_interval:
            return False

        # 生成总结
        summary = await self._generate_summary(messages_to_summarize)

        # 存入长期记忆
        new_memory = LongTermMemory(
            session_id=self.session_id,
            summary=summary,
            start_message_id=messages_to_summarize[0].id,
            end_message_id=messages_to_summarize[-1].id,
            tags=[],  # 可以用 LLM 提取标签
        )
        self.db.add(new_memory)
        await self.db.commit()

        return True

    async def _generate_summary(self, messages: List[Message]) -> str:
        """
        调用 LLM 生成对话总结
        
        总结要点：
        1. 发生了什么重要事件
        2. 了解到了用户的什么信息（喜好、性格、经历等）
        3. 两人的关系有什么变化
        4. 有什么需要记住的约定或承诺
        """
        conversation_text = "\n".join([
            f"{'用户' if m.role == 'user' else '你'}：{m.content}"
            for m in messages
        ])

        prompt = f"""
请阅读以下对话，然后生成一份简洁的"事件簿"记录。

对话内容：
{conversation_text}

请从以下几个方面总结（用中文，简洁明了，不超过 200 字）：
1. 这段对话的主要内容和发生的重要事件
2. 了解到对方的哪些信息（喜好、性格、近况等）
3. 两人关系有什么变化或进展
4. 有什么需要记住的约定、承诺或重要细节

直接输出总结内容，不要加标题。
"""

        try:
            response = await client.chat.completions.create(
                model=settings.SUMMARY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"总结生成失败: {e}")
            return "（总结生成失败）"

    async def build_memory_prompt(self) -> str:
        """
        构建记忆相关的 Prompt 片段
        包含长期记忆和当前的短期记忆说明
        """
        long_term = await self.get_long_term_memory()

        if not long_term:
            return ""

        return f"""
【重要回忆（事件簿）】
以下是你们之前对话中的重要事件和你需要记住的信息：
{long_term}

请结合这些回忆来回复，就像你真的记得一样。
如果用户提到了以前的事，你要表现出记得的样子。
不要说"根据我的记忆"之类的话，自然地融入对话。
"""
