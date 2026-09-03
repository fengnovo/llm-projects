"""
RAG 引擎核心

RAG 流程：
1. 用户提问
2. 向量化查询
3. 从向量库检索相关文档片段
4. 构建 Prompt（系统提示 + 检索到的文档 + 用户问题）
5. 调用 LLM 生成回答
6. 返回回答 + 引用来源
"""
from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI
from app.config import settings
from app.vectorstore import get_vector_store


client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
)


SYSTEM_PROMPT = """
你是一个知识助手，基于提供的参考资料来回答用户的问题。

【回答规则】
1. 只根据参考资料中的内容回答，不要编造信息
2. 如果参考资料中没有答案，直接说"抱歉，我在资料中没有找到相关信息"，不要猜测
3. 回答要准确、简洁、有条理
4. 如果参考资料中有多个相关内容，整合起来回答
5. 可以适当引用原文，但不要大段复制
6. 用中文回答

【参考资料格式】
每段资料前会标注来源和片段编号
"""


class RAGEngine:
    """RAG 问答引擎"""

    def __init__(self):
        self.vector_store = get_vector_store()

    def _build_context(self, docs: List[dict]) -> str:
        """构建参考资料上下文"""
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc["metadata"].get("source", "未知来源")
            chunk_idx = doc["metadata"].get("chunk_index", 0)
            parts.append(
                f"[资料 {i}] 来源：{source}（片段 {chunk_idx + 1}）\n{doc['content']}"
            )
        return "\n\n".join(parts)

    def _build_prompt(self, query: str, docs: List[dict]) -> List[Dict[str, str]]:
        """构建完整的对话消息"""
        context = self._build_context(docs)

        user_message = f"""
用户问题：{query}

【参考资料】
{context}

请根据参考资料回答用户的问题。如果资料中没有答案，请明确说明。
"""

        return [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_message.strip()},
        ]

    async def query(self, question: str, k: int = None) -> Dict:
        """
        RAG 查询（非流式）
        
        返回：
        {
            "answer": "回答内容",
            "sources": [...],  // 引用的来源
            "retrieved_docs": [...],  // 检索到的所有文档
        }
        """
        k = k or settings.RETRIEVE_TOP_K

        # 1. 检索相关文档
        docs = self.vector_store.similarity_search(question, k=k)

        if not docs:
            return {
                "answer": "抱歉，知识库中没有找到相关内容。",
                "sources": [],
                "retrieved_docs": [],
            }

        # 2. 构建 Prompt
        messages = self._build_prompt(question, docs)

        # 3. 调用 LLM
        try:
            response = await client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=messages,
                temperature=0.3,  # RAG 用低 temperature，更准确
                max_tokens=1000,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"生成回答时出错：{str(e)}"

        # 4. 整理来源（去重）
        sources = []
        seen = set()
        for doc in docs:
            source = doc["metadata"].get("source", "未知")
            if source not in seen:
                sources.append(source)
                seen.add(source)

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_docs": docs,
        }

    async def query_stream(self, question: str, k: int = None) -> AsyncGenerator[str, None]:
        """
        流式 RAG 查询
        """
        k = k or settings.RETRIEVE_TOP_K

        # 检索
        docs = self.vector_store.similarity_search(question, k=k)

        if not docs:
            yield "抱歉，知识库中没有找到相关内容。"
            return

        # 构建 Prompt
        messages = self._build_prompt(question, docs)

        # 流式调用
        try:
            stream = await client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=messages,
                stream=True,
                temperature=0.3,
                max_tokens=1000,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"\n\n[出错了：{str(e)}]"

    async def add_document(self, content: str, metadata: dict = None) -> List[str]:
        """添加单个文档到知识库"""
        from app.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        chunks = processor.split_text(content, source=metadata.get("source", "") if metadata else "")

        texts = [c["content"] for c in chunks]
        metas = [c["metadata"] for c in chunks]

        ids = self.vector_store.add_documents(texts, metas)
        return ids

    def get_stats(self) -> dict:
        """获取知识库统计"""
        return self.vector_store.get_collection_stats()
