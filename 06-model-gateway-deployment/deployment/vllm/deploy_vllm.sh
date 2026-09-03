#!/bin/bash
# ============================================================
# vLLM 部署脚本 - 启动开源大模型推理服务
#
# 前置要求:
#   - NVIDIA GPU (显存 >= 8GB 推荐)
#   - NVIDIA Driver + CUDA
#   - Python 3.10+
#
# 用法:
#   ./deploy_vllm.sh [模型名称] [GPU数量] [端口]
#
# 示例:
#   ./deploy_vllm.sh Qwen/Qwen2.5-7B-Instruct 1 8000
#   ./deploy_vllm.sh Qwen/Qwen2.5-14B-Instruct 2 8000
# ============================================================

set -e

MODEL_NAME=${1:-"Qwen/Qwen2.5-7B-Instruct"}
NUM_GPUS=${2:-1}
PORT=${3:-8000}
MODEL_LOCAL_PATH="/data/models/$(basename $MODEL_NAME)"

echo "=========================================="
echo "  vLLM 模型部署"
echo "=========================================="
echo ""
echo "模型:      $MODEL_NAME"
echo "GPU 数量:  $NUM_GPUS"
echo "端口:      $PORT"
echo ""

# 检查 GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ 未检测到 NVIDIA GPU，无法使用 vLLM"
    echo ""
    echo "💡 无 GPU 时，可以用 Ollama CPU 模式或者 Mock 服务来演示网关功能"
    echo "   Mock 服务: 见 deployment/mock_server/"
    echo "   Ollama:     见 deployment/ollama/"
    exit 1
fi

echo "GPU 信息:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# 检查 vLLM 是否已安装
if ! python -c "import vllm" &> /dev/null; then
    echo "未检测到 vLLM，正在安装..."
    pip install vllm
fi

# 检查模型是否已下载
if [ -d "$MODEL_LOCAL_PATH" ]; then
    echo "✅ 模型已存在: $MODEL_LOCAL_PATH"
    MODEL_PATH="$MODEL_LOCAL_PATH"
else
    echo "📥 模型将从 HuggingFace 下载..."
    MODEL_PATH="$MODEL_NAME"
fi

echo ""
echo "=========================================="
echo "  启动 vLLM 推理服务"
echo "=========================================="
echo ""
echo "API 地址:  http://localhost:$PORT/v1"
echo "模型名称:  $(basename $MODEL_NAME)-instruct"
echo "API Key:   任意字符串（本地部署不需要）"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动 vLLM OpenAI 兼容服务
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$(basename $MODEL_NAME | tr '[:upper:]' '[:lower:]')-instruct" \
    --tensor-parallel-size "$NUM_GPUS" \
    --port "$PORT" \
    --host 0.0.0.0 \
    --trust-remote-code \
    --gpu-memory-utilization 0.9 \
    --max-model-len 8192 \
    --enable-prefix-caching \
    --disable-log-stats
