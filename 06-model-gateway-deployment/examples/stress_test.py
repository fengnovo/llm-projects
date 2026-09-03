"""
压力测试脚本 - 测试模型网关的并发性能
用于验证限流、降级等机制是否正常工作
"""

import asyncio
import time
import random
import statistics
import httpx
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:4000")
MIDDLEWARE_URL = os.getenv("MIDDLEWARE_URL", "http://localhost:5000")
API_KEY = os.getenv("GATEWAY_API_KEY", "sk-gateway-demo-key-12345")

# 测试配置
CONCURRENT_REQUESTS = 20    # 并发数
TOTAL_REQUESTS = 100        # 总请求数
TEST_MODEL = "chat-default"  # 测试模型


async def make_request(client: httpx.AsyncClient, request_id: int, use_middleware: bool = False):
    """发送一个请求并统计耗时"""
    base_url = MIDDLEWARE_URL if use_middleware else GATEWAY_URL
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-API-Key": f"test-user-{request_id % 5}",  # 模拟多个用户
    }

    messages = [
        {"role": "user", "content": f"这是第 {request_id} 个测试请求，请简单回复。"}
    ]

    start_time = time.time()
    try:
        response = await client.post(
            f"{base_url}/v1/chat/completions",
            headers=headers,
            json={
                "model": TEST_MODEL,
                "messages": messages,
                "max_tokens": 50,
                "stream": False,
            },
            timeout=30.0,
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            return {
                "id": request_id,
                "status": "success",
                "elapsed": elapsed,
                "tokens": data.get("usage", {}).get("total_tokens", 0),
                "model": data.get("model", "unknown"),
            }
        else:
            return {
                "id": request_id,
                "status": "error",
                "elapsed": elapsed,
                "error": f"HTTP {response.status_code}",
                "detail": response.text[:200],
            }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "id": request_id,
            "status": "error",
            "elapsed": elapsed,
            "error": str(e),
        }


async def run_stress_test(use_middleware: bool = False):
    """运行压测"""
    print("=" * 60)
    print(f"  压力测试 - {'中间件' if use_middleware else '网关直连'}")
    print("=" * 60)
    print(f"并发数: {CONCURRENT_REQUESTS}")
    print(f"总请求: {TOTAL_REQUESTS}")
    print(f"目标地址: {MIDDLEWARE_URL if use_middleware else GATEWAY_URL}")
    print()

    results = []
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async def bounded_request(request_id):
        async with semaphore:
            return await make_request(client, request_id, use_middleware)

    async with httpx.AsyncClient() as client:
        start_time = time.time()

        tasks = [bounded_request(i) for i in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

    # 统计结果
    success = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]
    success_times = [r["elapsed"] for r in success]

    print(f"{' 结果统计 ':=^60}")
    print(f"总耗时:        {total_time:.2f} 秒")
    print(f"成功请求:      {len(success)} / {TOTAL_REQUESTS}")
    print(f"失败请求:      {len(errors)}")
    print(f"成功率:        {len(success)/TOTAL_REQUESTS*100:.1f}%")
    print(f"QPS:           {TOTAL_REQUESTS / total_time:.1f} req/s")
    print()

    if success_times:
        print(f"{' 延迟统计 ':=^60}")
        print(f"平均延迟:      {statistics.mean(success_times)*1000:.1f} ms")
        print(f"中位数延迟:    {statistics.median(success_times)*1000:.1f} ms")
        print(f"最小延迟:      {min(success_times)*1000:.1f} ms")
        print(f"最大延迟:      {max(success_times)*1000:.1f} ms")
        print(f"P95 延迟:      {sorted(success_times)[int(len(success_times)*0.95)]*1000:.1f} ms")
        print(f"P99 延迟:      {sorted(success_times)[int(len(success_times)*0.99)]*1000:.1f} ms")
        print()

    # Token 统计
    total_tokens = sum(r.get("tokens", 0) for r in success)
    print(f"{' Token 统计 ':=^60}")
    print(f"总 Token 数:   {total_tokens}")
    print(f"平均每请求:    {total_tokens / len(success) if success else 0:.0f} tokens")
    print(f"Token 吞吐:    {total_tokens / total_time:.0f} tokens/s")
    print()

    # 错误分类
    if errors:
        print(f"{' 错误分布 ':=^60}")
        error_types = defaultdict(int)
        for e in errors:
            error_types[e.get("error", "unknown")] += 1
        for err_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
            print(f"  {err_type}: {count} 次")
        print()

    # 模型分布
    model_dist = defaultdict(int)
    for r in success:
        model_dist[r.get("model", "unknown")] += 1
    if len(model_dist) > 1:
        print(f"{' 模型分布 ':=^60}")
        for model, count in sorted(model_dist.items(), key=lambda x: -x[1]):
            print(f"  {model}: {count} 次 ({count/len(success)*100:.1f}%)")
        print()

    return results


async def test_rate_limiting():
    """测试限流功能"""
    print("=" * 60)
    print("  限流测试")
    print("=" * 60)
    print("用大量并发请求测试中间件的限流机制")
    print()

    async with httpx.AsyncClient() as client:
        # 快速发送 50 个请求，看是否被限流
        tasks = []
        for i in range(50):
            tasks.append(make_request(client, i, use_middleware=True))

        results = await asyncio.gather(*tasks)

        rate_limited = [r for r in results if r["status"] == "error" and "429" in str(r.get("error", ""))]

        print(f"总请求: {len(results)}")
        print(f"被限流: {len(rate_limited)}")
        print(f"限流比例: {len(rate_limited)/len(results)*100:.1f}%")
        print()


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "gateway"

    if mode == "middleware":
        asyncio.run(run_stress_test(use_middleware=True))
    elif mode == "ratelimit":
        asyncio.run(test_rate_limiting())
    else:
        asyncio.run(run_stress_test(use_middleware=False))
