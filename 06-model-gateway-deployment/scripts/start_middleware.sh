#!/bin/bash
# ============================================================
# 启动网关中间件服务
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

PORT=${MIDDLEWARE_PORT:-5000}

echo "=========================================="
echo "  启动模型网关中间件"
echo "=========================================="
echo ""
echo "地址: http://localhost:$PORT"
echo "文档: http://localhost:$PORT/docs"
echo "上游网关: $GATEWAY_URL"
echo ""

# 安装依赖
if ! python -c "import fastapi" &> /dev/null; then
    echo "安装依赖中..."
    pip install -r middleware/requirements.txt
fi

cd middleware
python -m uvicorn gateway_middleware:app --host 0.0.0.0 --port "$PORT" --reload
