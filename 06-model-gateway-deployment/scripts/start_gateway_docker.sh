#!/bin/bash
# ============================================================
# 用 Docker Compose 一键启动完整网关栈
# 包含: LiteLLM 网关 + Redis + 模拟 LLM 服务
# 用法: ./start_gateway_docker.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR/gateway"

echo "=========================================="
echo "  Docker Compose 启动模型网关栈"
echo "=========================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 未检测到 Docker，请先安装 Docker Desktop"
    exit 1
fi

# 复制环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" .env
    echo "✅ 已加载环境变量"
else
    echo "⚠️  未找到 .env 文件，将使用默认配置"
fi

echo ""
echo "启动服务中..."
echo ""

docker compose up -d

echo ""
echo "=========================================="
echo "  ✅  服务启动完成"
echo "=========================================="
echo ""
echo "网关地址:   http://localhost:4000"
echo "管理后台:   http://localhost:4000/ui  (key: sk-admin-gateway-key-change-me)"
echo "API 文档:   http://localhost:4000/docs"
echo "模拟LLM:    http://localhost:8000 (OpenAI 兼容)"
echo "Redis:      localhost:6379"
echo ""
echo "查看日志:   docker compose logs -f litellm-proxy"
echo "停止服务:   docker compose down"
echo ""
