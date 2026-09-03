# vLLM 部署指南

## 简介

vLLM 是一个高性能的大模型推理框架，核心特性：
- **PagedAttention**：高效的 KV Cache 管理，显存利用率高
- **连续批处理**（Continuous Batching）：高并发下吞吐量大
- **OpenAI 兼容 API**：无缝替换 OpenAI 接口

## 硬件要求

| 模型大小 | 显存需求（FP16） | 显存需求（AWQ 4bit） | 推荐 GPU |
|----------|-----------------|---------------------|----------|
| 7B | ~14 GB | ~4 GB | RTX 3090/4090 |
| 14B | ~28 GB | ~8 GB | RTX 4090 x2 / A100 40G |
| 32B | ~64 GB | ~18 GB | A100 80G |
| 72B | ~144 GB | ~40 GB | A100 80G x2 |

## 快速部署（云 GPU）

如果没有本地 GPU，可以用云 GPU 平台：

### 推荐平台
- **AutoDL**：https://www.autodl.com/ （便宜，按小时计费）
- **恒源云**：https://www.gpushare.com/
- **阿里云 PAI**：企业级

### 部署步骤

1. 创建一台 RTX 4090 实例（镜像选 PyTorch + CUDA）
2. 上传 `deploy_vllm.sh` 脚本
3. 执行：
   ```bash
   chmod +x deploy_vllm.sh
   ./deploy_vllm.sh Qwen/Qwen2.5-7B-Instruct 1 8000
   ```
4. 等模型下载完成（几分钟到几十分钟）
5. 测试接口：
   ```bash
   curl http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer dummy" \
     -d '{
       "model": "qwen2.5-7b-instruct",
       "messages": [{"role": "user", "content": "你好"}]
     }'
   ```

## Docker 部署 vLLM

```bash
# 拉取 vLLM 镜像
docker pull vllm/vllm-openai:latest

# 启动容器
docker run --gpus all \
  -v /data/models:/models \
  -p 8000:8000 \
  --name vllm-server \
  vllm/vllm-openai:latest \
  --model /models/Qwen2.5-7B-Instruct \
  --served-model-name qwen2.5-7b-instruct \
  --tensor-parallel-size 1
```

## 性能优化技巧

### 1. 量化（省显存）
```bash
# AWQ 4bit 量化，7B 模型只需 4~5GB 显存
python -m vllm.entrypoints.openai.api_server \
  --model TheBloke/Qwen2.5-7B-Instruct-AWQ \
  --quantization awq \
  --gpu-memory-utilization 0.95
```

### 2. 开启前缀缓存
```bash
--enable-prefix-caching
```
相同前缀（比如 System Prompt）会被缓存，大幅加速多轮对话。

### 3. 调整最大上下文长度
```bash
--max-model-len 4096   # 设小一点，省显存
```

### 4. 张量并行（多 GPU）
```bash
--tensor-parallel-size 2   # 用 2 张 GPU
```

## 接入模型网关

vLLM 启动后，在 `gateway/litellm_config.yaml` 中添加：

```yaml
model_list:
  - model_name: qwen2.5-7b-local
    litellm_params:
      model: openai/qwen2.5-7b-instruct
      api_base: "http://localhost:8000/v1"
      api_key: "dummy"
```

然后业务方调用网关的 `qwen2.5-7b-local` 模型名即可，完全透明。

## 监控 vLLM

vLLM 自带 Prometheus 指标：

```bash
# 访问指标端点
curl http://localhost:8000/metrics
```

关键指标：
- `vllm:avg_generation_throughput_tokens_per_second`：生成吞吐量
- `vllm:avg_prompt_throughput_tokens_per_second`：Prompt 处理吞吐量
- `vllm:gpu_cache_usage_perc`：KV Cache 使用率
- `vllm:num_requests_running`：当前处理的请求数
