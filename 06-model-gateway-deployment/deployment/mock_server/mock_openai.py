"""
Mock LLM Server - 模拟 OpenAI 兼容接口
用于无 GPU 环境下演示模型网关功能

功能:
- /v1/chat/completions  - 聊天补全（支持流式）
- /v1/completions       - 文本补全
- /v1/models            - 模型列表
- /v1/embeddings        - Embedding
- /health               - 健康检查
"""

import asyncio
import json
import time
import random
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Mock LLM Server", version="1.0.0")


# ============ 数据模型 ============

class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "mock-model"
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 512
    stream: bool = False
    top_p: float = 1.0


class CompletionRequest(BaseModel):
    model: str = "mock-model"
    prompt: str
    max_tokens: int = 512
    stream: bool = False
    temperature: float = 0.7


class EmbeddingRequest(BaseModel):
    model: str = "mock-embedding"
    input: str | List[str]


# ============ Mock 回复生成 ============

MOCK_RESPONSES = {
    "你好": "你好呀！很高兴见到你~ 我是一个 Mock AI 助手，运行在本地模型上。有什么我可以帮你的吗？",
    "你是谁": "我是 Mock LLM，一个模拟的大语言模型。我用来测试模型网关和系统集成，不需要真实 GPU 就能运行。",
    "介绍一下你自己": "我是 Mock LLM Server，提供 OpenAI 兼容的 API 接口。\n\n我的作用是：\n1. 在没有 GPU 的环境中模拟 LLM 服务\n2. 测试模型网关的路由、限流、降级功能\n3. 作为开发环境的轻量替代\n\n你可以通过 LiteLLM 网关来调用我~",
    "天气": "今天天气晴朗，气温 25°C，适合出门散步！☀️\n\n（这是 Mock 数据，真实场景下应该调用天气 API）",
    "时间": f"现在的时间是 {time.strftime('%Y-%m-%d %H:%M:%S')}",
    "笑话": "程序员的幽默：\n\n为什么程序员喜欢黑暗模式？\n因为 light attracts bugs. 🐛",
    "默认": "这是 Mock LLM 的默认回复。\n\n我可以模拟各种 AI 回复场景，用来测试：\n- 模型网关的路由功能\n- 流式输出\n- Token 统计\n- 错误处理\n\n试试问我「你是谁」「讲个笑话」「今天天气怎么样」~",
}


def get_mock_response(user_message: str) -> str:
    """根据用户输入返回对应的 Mock 回复"""
    msg = user_message.lower()
    for keyword, response in MOCK_RESPONSES.items():
        if keyword in msg:
            return response
    return MOCK_RESPONSES["默认"]


def generate_stream_tokens(text: str, delay: float = 0.03):
    """模拟流式输出，逐字返回"""
    for char in text:
        yield char
        time.sleep(delay)


# ============ 聊天补全接口 ============

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """聊天补全 - OpenAI 兼容接口"""

    # 获取最后一条用户消息
    user_msg = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    response_text = get_mock_response(user_msg)

    if request.stream:
        # 流式响应
        async def stream_generator():
            for i, char in enumerate(response_text):
                chunk = {
                    "id": f"chatcmpl-mock-{int(time.time())}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": char},
                        "finish_reason": None if i < len(response_text) - 1 else "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.03)
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # 非流式响应
        # 模拟延迟
        await asyncio.sleep(0.5)
        return {
            "id": f"chatcmpl-mock-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": sum(len(m.content) for m in request.messages) // 4 + 10,
                "completion_tokens": len(response_text) // 4 + 5,
                "total_tokens": sum(len(m.content) for m in request.messages) // 4 + len(response_text) // 4 + 15
            }
        }


# ============ 文本补全接口 ============

@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """文本补全 - OpenAI 兼容接口"""
    response_text = f"\n\n这是对 '{request.prompt[:30]}...' 的模拟补全结果。\n\nMock LLM 正在工作中~"

    if request.stream:
        async def stream_generator():
            for i, char in enumerate(response_text):
                chunk = {
                    "id": f"cmpl-mock-{int(time.time())}",
                    "object": "text_completion",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "text": char,
                        "finish_reason": None if i < len(response_text) - 1 else "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.02)
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        await asyncio.sleep(0.3)
        return {
            "id": f"cmpl-mock-{int(time.time())}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "text": response_text,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(request.prompt) // 4,
                "completion_tokens": len(response_text) // 4,
                "total_tokens": len(request.prompt) // 4 + len(response_text) // 4
            }
        }


# ============ Embedding 接口 ============

@app.post("/v1/embeddings")
async def embeddings(request: EmbeddingRequest):
    """Embedding 接口 - 返回随机向量（模拟）"""
    texts = request.input if isinstance(request.input, list) else [request.input]

    data = []
    for i, text in enumerate(texts):
        # 生成一个 1536 维的随机向量（模拟 text-embedding-ada-002）
        embedding = [random.uniform(-1, 1) for _ in range(1536)]
        # 归一化
        norm = sum(x * x for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]
        data.append({
            "object": "embedding",
            "index": i,
            "embedding": embedding
        })

    return {
        "object": "list",
        "data": data,
        "model": request.model,
        "usage": {
            "prompt_tokens": sum(len(t) for t in texts) // 4,
            "total_tokens": sum(len(t) for t in texts) // 4
        }
    }


# ============ 模型列表 ============

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "mock-model",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "mock"
            },
            {
                "id": "qwen2.5-7b-instruct",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "mock"
            }
        ]
    }


# ============ 健康检查 ============

@app.get("/health")
async def health():
    return {"status": "ok", "model": "mock-model"}


@app.get("/")
async def root():
    return {
        "name": "Mock LLM Server",
        "version": "1.0.0",
        "endpoints": [
            "POST /v1/chat/completions",
            "POST /v1/completions",
            "POST /v1/embeddings",
            "GET /v1/models",
            "GET /health"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
