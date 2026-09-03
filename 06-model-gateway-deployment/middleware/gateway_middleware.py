"""
模型网关中间件服务
==================

在 LiteLLM 网关之上增加一层业务级别的控制：
- 限流（Rate Limiting）：基于 API Key 的 QPS 和 Token 限制
- 降级（Fallback）：主模型故障时自动切换到备用模型
- 灰度发布（Canary）：按用户/比例切流到新模型
- 成本统计：按用户/模型维度统计 Token 用量和费用
- 监控指标：Prometheus 格式指标输出

架构:
  业务方 → 本中间件 → LiteLLM 网关 → 各种模型供应商
"""

import asyncio
import json
import time
import uuid
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import httpx
import redis
from fastapi import FastAPI, HTTPException, Request, Response, Header
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

# ============ 配置 ============

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:4000")
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY", "sk-gateway-demo-key-12345")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MIDDLEWARE_PORT = int(os.getenv("MIDDLEWARE_PORT", "5000"))

# 限流配置（可以从配置中心动态拉取）
RATE_LIMITS = {
    "default": {
        "qps": 10,           # 每秒请求数
        "rpm": 300,          # 每分钟请求数
        "tpm": 100000,       # 每分钟 token 数
        "daily_tokens": 1000000,  # 每日 token 上限
    },
    "premium": {
        "qps": 50,
        "rpm": 1000,
        "tpm": 500000,
        "daily_tokens": 10000000,
    }
}

# 降级配置
FALLBACK_CHAIN = {
    "chat-default": ["gpt-4o-mini", "qwen-turbo", "deepseek-chat", "chat-local"],
    "chat-pro": ["gpt-4o", "chat-default"],
    "chat-local": ["qwen2.5-7b-local", "llama3.2-3b-ollama"],
}

# 灰度配置
CANARY_CONFIG = {
    "chat-default": {
        "new_model": "gpt-4o",       # 灰度目标模型
        "percentage": 20,            # 灰度比例（%）
        "enabled": False,             # 开关
        "user_whitelist": [],         # 白名单用户 ID（强制走新模型）
        "user_blacklist": [],         # 黑名单用户 ID（强制走旧模型）
    }
}


# ============ 全局对象 ============

redis_client = None
httpx_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, httpx_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Redis 连接成功")
    except Exception as e:
        print(f"⚠️  Redis 连接失败: {e}，限流功能将不可用")
        redis_client = None

    httpx_client = httpx.AsyncClient(timeout=60.0)
    yield
    await httpx_client.aclose()
    if redis_client:
        redis_client.close()


app = FastAPI(title="模型网关中间件", lifespan=lifespan, version="1.0.0")


# ============ 数据模型 ============

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 512
    stream: bool = False
    user_id: Optional[str] = None
    api_key_tier: str = "default"   # API 等级: default / premium


# ============ 限流工具 ============

class RateLimiter:
    """基于 Redis 的滑动窗口限流"""

    @staticmethod
    def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
        """
        检查是否超过限流
        返回 True 表示通过（没超限），False 表示超限
        """
        if not redis_client:
            return True  # Redis 不可用时放行

        now = time.time()
        window_start = now - window_seconds
        pipe = redis_client.pipeline()

        # 清理窗口外的数据
        pipe.zremrangebyscore(key, 0, window_start)
        # 统计窗口内的请求数
        pipe.zcard(key)
        # 添加当前请求
        pipe.zadd(key, {str(uuid.uuid4()): now})
        # 设置过期时间
        pipe.expire(key, window_seconds)

        results = pipe.execute()
        count = results[1]

        return count < limit

    @staticmethod
    def check_qps(api_key: str, tier: str = "default") -> bool:
        """检查 QPS 限制"""
        limits = RATE_LIMITS.get(tier, RATE_LIMITS["default"])
        key = f"rate:qps:{api_key}"
        return RateLimiter.check_rate_limit(key, limits["qps"], 1)

    @staticmethod
    def check_rpm(api_key: str, tier: str = "default") -> bool:
        """检查 RPM 限制"""
        limits = RATE_LIMITS.get(tier, RATE_LIMITS["default"])
        key = f"rate:rpm:{api_key}"
        return RateLimiter.check_rate_limit(key, limits["rpm"], 60)

    @staticmethod
    def check_daily_tokens(api_key: str, tokens: int, tier: str = "default") -> bool:
        """检查每日 Token 上限"""
        if not redis_client:
            return True

        limits = RATE_LIMITS.get(tier, RATE_LIMITS["default"])
        key = f"rate:daily:{api_key}:{time.strftime('%Y%m%d')}"

        current = int(redis_client.get(key) or 0)
        if current + tokens > limits["daily_tokens"]:
            return False

        redis_client.incrby(key, tokens)
        redis_client.expire(key, 86400)
        return True


# ============ 灰度路由 ============

def canary_route(model: str, user_id: Optional[str] = None) -> str:
    """
    灰度发布路由
    根据配置决定走新模型还是旧模型
    """
    config = CANARY_CONFIG.get(model)
    if not config or not config.get("enabled", False):
        return model

    # 白名单用户强制走新模型
    if user_id and user_id in config.get("user_whitelist", []):
        print(f"[灰度] 用户 {user_id} 在白名单，路由到 {config['new_model']}")
        return config["new_model"]

    # 黑名单用户强制走旧模型
    if user_id and user_id in config.get("user_blacklist", []):
        print(f"[灰度] 用户 {user_id} 在黑名单，保持 {model}")
        return model

    # 按比例随机
    percentage = config.get("percentage", 0)
    if random.randint(1, 100) <= percentage:
        print(f"[灰度] 命中 {percentage}% 比例，路由到 {config['new_model']}")
        return config["new_model"]

    return model


# ============ 降级逻辑 ============

async def chat_with_fallback(request_data: dict, api_key: str) -> tuple[Any, str]:
    """
    带降级的聊天请求
    依次尝试降级链中的模型，直到成功或全部失败
    """
    model = request_data["model"]
    fallback_chain = FALLBACK_CHAIN.get(model, [model])

    last_error = None
    for try_model in fallback_chain:
        try:
            print(f"[降级] 尝试模型: {try_model}")
            req_data = {**request_data, "model": try_model}

            response = await httpx_client.post(
                f"{GATEWAY_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GATEWAY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=req_data,
            )

            if response.status_code == 200:
                if last_error:
                    print(f"[降级] 从 {fallback_chain[0]} 降级到 {try_model} 成功")
                return response, try_model
            else:
                last_error = f"HTTP {response.status_code}: {response.text}"
                print(f"[降级] 模型 {try_model} 失败: {last_error}")

        except Exception as e:
            last_error = str(e)
            print(f"[降级] 模型 {try_model} 异常: {e}")

    raise HTTPException(status_code=503, detail=f"所有模型都失败了，最后错误: {last_error}")


# ============ 成本统计 ============

def record_usage(api_key: str, model: str, prompt_tokens: int, completion_tokens: int):
    """记录 Token 用量"""
    if not redis_client:
        return

    today = time.strftime('%Y%m%d')
    pipe = redis_client.pipeline()

    # 按 API Key 统计
    pipe.hincrby(f"usage:key:{api_key}:{today}", "prompt_tokens", prompt_tokens)
    pipe.hincrby(f"usage:key:{api_key}:{today}", "completion_tokens", completion_tokens)
    pipe.hincrby(f"usage:key:{api_key}:{today}", "requests", 1)

    # 按模型统计
    pipe.hincrby(f"usage:model:{model}:{today}", "prompt_tokens", prompt_tokens)
    pipe.hincrby(f"usage:model:{model}:{today}", "completion_tokens", completion_tokens)
    pipe.hincrby(f"usage:model:{model}:{today}", "requests", 1)

    pipe.execute()


# ============ 聊天接口 ============

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    x_api_key: str = Header(default="anonymous"),
):
    """
    聊天补全接口（带限流、降级、灰度）

    业务方调用这个接口，不用关心底层用哪个模型
    """
    tier = request.api_key_tier

    # 1. 限流检查
    if not RateLimiter.check_qps(x_api_key, tier):
        raise HTTPException(status_code=429, detail="QPS 超限，请稍后再试")
    if not RateLimiter.check_rpm(x_api_key, tier):
        raise HTTPException(status_code=429, detail="RPM 超限，请稍后再试")

    # 2. 灰度路由
    actual_model = canary_route(request.model, request.user_id)

    # 3. 准备请求数据
    request_dict = request.model_dump()
    request_dict["model"] = actual_model
    request_dict.pop("user_id", None)
    request_dict.pop("api_key_tier", None)

    # 4. 带降级调用
    if request.stream:
        # 流式响应
        response, used_model = await chat_with_fallback(request_dict, x_api_key)

        async def stream_with_stats():
            completion_text = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        yield line
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                            completion_text += chunk["choices"][0]["delta"]["content"]
                    except:
                        pass
                yield f"{line}\n"

            # 记录用量（估算）
            prompt_tokens = sum(len(m.content) for m in request.messages) // 4
            completion_tokens = len(completion_text) // 4
            record_usage(x_api_key, used_model, prompt_tokens, completion_tokens)

        return StreamingResponse(stream_with_stats(), media_type="text/event-stream")
    else:
        # 非流式响应
        response, used_model = await chat_with_fallback(request_dict, x_api_key)
        result = response.json()

        # 记录用量
        usage = result.get("usage", {})
        record_usage(
            x_api_key,
            used_model,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0)
        )

        # 在返回结果中加上实际使用的模型
        result["used_model"] = used_model
        return result


# ============ 管理接口 ============

@app.get("/admin/usage/{api_key}")
async def get_usage(api_key: str):
    """查询指定 API Key 的今日用量"""
    if not redis_client:
        return {"error": "Redis 不可用"}

    today = time.strftime('%Y%m%d')
    key = f"usage:key:{api_key}:{today}"
    data = redis_client.hgetall(key)
    return {
        "api_key": api_key,
        "date": today,
        "prompt_tokens": int(data.get("prompt_tokens", 0)),
        "completion_tokens": int(data.get("completion_tokens", 0)),
        "requests": int(data.get("requests", 0)),
    }


@app.get("/admin/model-usage/{model}")
async def get_model_usage(model: str):
    """查询指定模型的今日用量"""
    if not redis_client:
        return {"error": "Redis 不可用"}

    today = time.strftime('%Y%m%d')
    key = f"usage:model:{model}:{today}"
    data = redis_client.hgetall(key)
    return {
        "model": model,
        "date": today,
        "prompt_tokens": int(data.get("prompt_tokens", 0)),
        "completion_tokens": int(data.get("completion_tokens", 0)),
        "requests": int(data.get("requests", 0)),
    }


@app.get("/admin/canary/config")
async def get_canary_config():
    """获取灰度配置"""
    return CANARY_CONFIG


@app.post("/admin/canary/config")
async def update_canary(config: dict):
    """更新灰度配置（生产环境应该从配置中心读取）"""
    global CANARY_CONFIG
    CANARY_CONFIG.update(config)
    return {"status": "ok", "config": CANARY_CONFIG}


@app.get("/health")
async def health():
    """健康检查"""
    redis_status = "ok" if redis_client else "unavailable"
    return {
        "status": "ok",
        "middleware": "running",
        "gateway_url": GATEWAY_URL,
        "redis": redis_status,
    }


@app.get("/")
async def root():
    return {
        "name": "模型网关中间件",
        "version": "1.0.0",
        "features": [
            "限流 (QPS/RPM/Daily Token)",
            "自动降级 (Fallback Chain)",
            "灰度发布 (Canary Release)",
            "用量统计 (Usage Tracking)",
        ],
        "endpoints": {
            "chat": "POST /v1/chat/completions",
            "usage": "GET /admin/usage/{api_key}",
            "model_usage": "GET /admin/model-usage/{model}",
            "canary": "GET /admin/canary/config",
            "health": "GET /health",
        }
    }


if __name__ == "__main__":
    import uvicorn
    import random
    uvicorn.run(app, host="0.0.0.0", port=MIDDLEWARE_PORT, reload=True)
