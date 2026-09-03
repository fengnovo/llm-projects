#!/bin/bash
# ============================================================
# 启动 Mock LLM 服务（无 GPU 环境下演示用）
# 提供 OpenAI 兼容接口，可以接入模型网关
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=${1:-8000}

cd "$SCRIPT_DIR"

echo "=========================================="
echo "  启动 Mock LLM 服务"
echo "=========================================="
echo ""
echo "地址: http://localhost:$PORT"
echo "文档: http://localhost:$PORT/docs"
echo ""

# 检查依赖
if ! python -c "import fastapi" &> /dev/null; then
    echo "安装依赖中..."
    pip install fastapi uvicorn pydantic
fi

echo "服务启动中..."
echo "按 Ctrl+C 停止"
echo ""

python -m uvicorn mock_openai:app --host 0.0.0.0 --port "$PORT" --reload
