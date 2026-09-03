#!/bin/bash
# ============================================================
# 启动模型网关（LiteLLM Proxy）
# 用法: ./start_gateway.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR/gateway"

# 加载环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

echo "=========================================="
echo "  启动 LiteLLM 模型网关"
echo "=========================================="
echo ""
echo "配置文件: gateway/litellm_config.yaml"
echo "网关地址: http://localhost:${GATEWAY_PORT:-4000}"
echo "管理后台: http://localhost:${GATEWAY_PORT:-4000}/ui"
echo "API 文档: http://localhost:${GATEWAY_PORT:-4000}/docs"
echo ""

# 检查是否安装了 litellm
if ! command -v litellm &> /dev/null; then
    echo "未检测到 litellm，正在安装..."
    pip install 'litellm[proxy]'
fi

# 启动网关
litellm --config litellm_config.yaml --port ${GATEWAY_PORT:-4000} --detailed_debug
