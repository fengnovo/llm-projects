"""
成本计算工具
估算不同模型、不同用量下的成本
帮助做成本控制决策
"""

# 模型定价表（参考市场价，单位：美元 / 1K tokens）
MODEL_PRICING = {
    # 云端模型
    "gpt-4o": {
        "input": 0.005,    # 输入：$5 / 1M tokens
        "output": 0.015,   # 输出：$15 / 1M tokens
        "type": "cloud"
    },
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.0006,
        "type": "cloud"
    },
    "deepseek-chat": {
        "input": 0.00014,
        "output": 0.00028,
        "type": "cloud"
    },
    "qwen-turbo": {
        "input": 0.00008,
        "output": 0.0002,
        "type": "cloud"
    },
    # 私有化部署模型（按 GPU 成本估算）
    "qwen2.5-7b-local": {
        "input": 0.00003,    # 约为云端的 1/5 ~ 1/10
        "output": 0.00006,
        "type": "local",
        "gpu_hourly_cost": 2.0,   # 4090 云 GPU 约 $2/小时
        "tokens_per_hour": 5000000,  # 估算每小时处理 token 数
    },
    "llama3.2-3b-ollama": {
        "input": 0.00002,
        "output": 0.00004,
        "type": "local",
        "gpu_hourly_cost": 1.0,
        "tokens_per_hour": 3000000,
    },
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> dict:
    """计算调用成本"""
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return {"error": f"未知模型: {model}"}

    input_cost = input_tokens / 1000 * pricing["input"]
    output_cost = output_tokens / 1000 * pricing["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "type": pricing["type"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": total_cost,
    }


def compare_models(input_tokens: int, output_tokens: int):
    """对比不同模型的成本"""
    print(f"\n{' 模型成本对比 ':=^60}")
    print(f"输入 Token: {input_tokens:,}")
    print(f"输出 Token: {output_tokens:,}")
    print(f"{'─' * 60}")
    print(f"{'模型':<25} {'类型':<8} {'成本(USD)':<12} {'相对比例'}")
    print(f"{'─' * 60}")

    costs = []
    for model, pricing in MODEL_PRICING.items():
        result = calculate_cost(model, input_tokens, output_tokens)
        if "error" not in result:
            costs.append(result)

    costs.sort(key=lambda x: x["total_cost_usd"])

    base_cost = costs[0]["total_cost_usd"]
    for c in costs:
        ratio = c["total_cost_usd"] / base_cost
        type_label = "云端" if c["type"] == "cloud" else "私有化"
        print(f"{c['model']:<25} {type_label:<8} ${c['total_cost_usd']:<11.6f} {ratio:.1f}x")

    print(f"{'─' * 60}")
    print()


def monthly_cost_estimate(daily_requests: int, avg_input: int, avg_output: int):
    """估算月度成本"""
    print(f"\n{' 月度成本估算 ':=^60}")
    print(f"日均请求: {daily_requests:,}")
    print(f"平均输入: {avg_input:,} tokens")
    print(f"平均输出: {avg_output:,} tokens")
    print(f"{'─' * 60}")
    print(f"{'模型':<25} {'月成本(USD)':<14} {'月成本(CNY)':<14}")
    print(f"{'─' * 60}")

    monthly_requests = daily_requests * 30
    total_input = monthly_requests * avg_input
    total_output = monthly_requests * avg_output

    costs = []
    for model in MODEL_PRICING:
        result = calculate_cost(model, total_input, total_output)
        if "error" not in result:
            costs.append(result)

    costs.sort(key=lambda x: x["total_cost_usd"])

    for c in costs:
        usd = c["total_cost_usd"]
        cny = usd * 7.2  # 假设汇率 7.2
        print(f"{c['model']:<25} ${usd:<13,.2f} ¥{cny:<13,.2f}")

    print(f"{'─' * 60}")
    print()


def token_saving_calculation(original_tokens: int, compressed_ratio: float):
    """计算 Prompt 压缩节省的成本"""
    print(f"\n{' Prompt 压缩成本节省 ':=^60}")
    print(f"原始 Token: {original_tokens:,}")
    print(f"压缩率: {compressed_ratio*100:.0f}%")
    print(f"{'─' * 60}")

    compressed = int(original_tokens * (1 - compressed_ratio))
    saved = original_tokens - compressed

    print(f"压缩后: {compressed:,} tokens")
    print(f"节省: {saved:,} tokens")
    print()
    print(f"各模型每次调用节省:")
    print(f"{'─' * 60}")

    for model, pricing in MODEL_PRICING.items():
        if pricing["type"] == "cloud":
            saved_cost = saved / 1000 * pricing["input"]
            print(f"  {model:<25} 节省 ${saved_cost:.6f} / 次")

    print(f"{'─' * 60}")
    print()


def kv_cache_benefit(cache_hit_rate: float, total_requests: int, prompt_tokens: int):
    """计算 KV Cache 的收益"""
    print(f"\n{' KV Cache 收益分析 ':=^60}")
    print(f"缓存命中率: {cache_hit_rate*100:.0f}%")
    print(f"总请求数: {total_requests:,}")
    print(f"平均 Prompt: {prompt_tokens:,} tokens")
    print(f"{'─' * 60}")

    cached_requests = int(total_requests * cache_hit_rate)
    # 假设缓存命中能节省 50% 的 Prompt 处理时间
    saved_time_ratio = cache_hit_rate * 0.5
    # 吞吐量提升
    throughput_improvement = 1 / (1 - saved_time_ratio)

    print(f"缓存命中请求: {cached_requests:,}")
    print(f"预计吞吐提升: {throughput_improvement:.2f}x")
    print(f"相当于节省 {saved_time_ratio*100:.1f}% 的计算资源")
    print()

    # 成本节省（按本地 GPU 计算）
    for model, pricing in MODEL_PRICING.items():
        if pricing["type"] == "local" and "gpu_hourly_cost" in pricing:
            hourly_cost = pricing["gpu_hourly_cost"]
            saved_cost = hourly_cost * saved_time_ratio
            print(f"  {model:<25} 每小时节省 ${saved_cost:.2f}")

    print(f"{'─' * 60}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  💰 模型成本计算器")
    print("=" * 60)

    # 1. 单次调用成本对比
    compare_models(
        input_tokens=1000,
        output_tokens=500
    )

    # 2. 月度成本估算
    monthly_cost_estimate(
        daily_requests=10000,
        avg_input=500,
        avg_output=300
    )

    # 3. Prompt 压缩收益
    token_saving_calculation(
        original_tokens=2000,
        compressed_ratio=0.4  # 压缩 40%
    )

    # 4. KV Cache 收益
    kv_cache_benefit(
        cache_hit_rate=0.6,
        total_requests=100000,
        prompt_tokens=800
    )

    print("✅ 成本分析完成！")
    print()
