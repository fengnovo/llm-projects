#!/bin/bash
# ============================================================
# Ollama 部署脚本 - 快速本地运行开源模型（支持 CPU/GPU）
#
# 适合场景:
#   - 没有 GPU，用 CPU 跑小模型做演示
#   - Mac 电脑（支持 Apple Silicon 加速）
#   - 快速验证模型效果
#
# 用法:
#   ./deploy_ollama.sh [模型名称]
#
# 示例:
#   ./deploy_ollama.sh llama3.2:3b
#   ./deploy_ollama.sh qwen2.5:7b
# ============================================================

set -e

MODEL_NAME=${1:-"llama3.2:3b"}

echo "=========================================="
echo "  Ollama 模型部署"
echo "=========================================="
echo ""
echo "模型: $MODEL_NAME"
echo ""

# 检查 Ollama 是否已安装
if ! command -v ollama &> /dev/null; then
    echo "未检测到 Ollama，正在安装..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "请访问 https://ollama.ai/download 下载 Ollama.app"
        echo "安装完成后重新运行此脚本"
        open "https://ollama.ai/download"
        exit 1
    else
        # Linux
        curl -fsSL https://ollama.com/install.sh | sh
    fi
fi

echo "✅ Ollama 已安装"
echo ""

# 启动 Ollama 服务（后台运行）
if ! pgrep -x "ollama" > /dev/null; then
    echo "启动 Ollama 服务..."
    ollama serve &
    sleep 3
fi

echo "✅ Ollama 服务运行中"
echo ""

# 拉取模型
echo "📥 拉取模型 $MODEL_NAME ..."
ollama pull "$MODEL_NAME"

echo ""
echo "=========================================="
echo "  ✅  模型部署完成"
echo "=========================================="
echo ""
echo "API 地址:  http://localhost:11434"
echo "模型名称:  $MODEL_NAME"
echo ""
echo "测试命令:"
echo "  ollama run $MODEL_NAME '你好'"
echo ""
echo "OpenAI 兼容 API:"
echo "  curl http://localhost:11434/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\": \"$MODEL_NAME\", \"messages\": [{\"role\": \"user\", \"content\": \"你好\"}]}'"
echo ""

# 列出已安装的模型
echo "已安装的模型:"
ollama list
