# Ollama 部署指南

## 简介

Ollama 是一个非常易用的本地大模型运行工具，特点：
- **一键安装**：下载即用，不用配环境
- **跨平台**：支持 macOS、Linux、Windows
- **Apple Silicon 优化**：Mac 上也能跑得动
- **模型库丰富**：主流开源模型都有

适合用来做本地开发、测试、演示。

## 安装

### macOS
1. 访问 https://ollama.ai/download
2. 下载 Ollama.app 并安装
3. 打开终端，运行 `ollama --version` 验证

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
访问 https://ollama.ai/download 下载安装包

## 常用模型推荐

| 模型 | 参数 | 显存需求 | 适用场景 |
|------|------|----------|----------|
| llama3.2:3b | 3B | ~2GB | 快速测试、简单对话 |
| qwen2.5:7b | 7B | ~5GB | 中文效果好，日常对话 |
| qwen2.5:14b | 14B | ~10GB | 高质量对话 |
| deepseek-v2:16b | 16B | ~12GB | 代码 + 对话 |
| mistral:7b | 7B | ~5GB | 英文对话 |

## 常用命令

```bash
# 拉取模型
ollama pull qwen2.5:7b

# 运行模型（交互式）
ollama run qwen2.5:7b

# 列出已安装模型
ollama list

# 删除模型
ollama rm qwen2.5:7b

# 查看运行中的模型
ollama ps

# 启动服务（默认端口 11434）
ollama serve
```

## API 调用

Ollama 提供 OpenAI 兼容的 API：

```bash
# 聊天补全
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {"role": "system", "content": "你是一个 helpful 的助手"},
      {"role": "user", "content": "你好，介绍一下你自己"}
    ],
    "stream": true
  }'

# 文本补全
curl http://localhost:11434/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "prompt": "写一首关于秋天的诗：",
    "stream": true
  }'
```

## 接入模型网关

在 `gateway/litellm_config.yaml` 中添加：

```yaml
model_list:
  - model_name: qwen2.5-7b-ollama
    litellm_params:
      model: ollama/qwen2.5:7b
      api_base: "http://localhost:11434"
```

然后业务方调用网关的 `qwen2.5-7b-ollama` 即可。

## 自定义模型（Modelfile）

你可以基于基础模型创建自己的角色模型：

```dockerfile
# Modelfile
FROM qwen2.5:7b

# 设置 System Prompt
SYSTEM """
你是小猫喵喵，一只可爱的猫咪AI。
- 说话结尾带"喵~"
- 喜欢撒娇，性格活泼
- 对主人很忠诚
"""

# 参数设置
PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
```

创建并运行：
```bash
ollama create kitty -f Modelfile
ollama run kitty
```

## 性能优化

### 调整上下文窗口
```bash
# 运行时指定
ollama run qwen2.5:7b "--num_ctx 8192"
```

### 调整并发数
```bash
# 设置环境变量
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2
ollama serve
```

### GPU 内存设置
```bash
export OLLAMA_GPU_LAYERS=35   # 加载到 GPU 的层数
```
