# 项目 1：AI 聊天助手

> 入门级项目 · Next.js + Vercel AI SDK · 前端友好

## 项目简介

一个简洁的 AI 聊天应用，支持流式输出、多轮对话、Markdown 渲染。使用你熟悉的 TypeScript / React 技术栈，快速建立 AI 应用开发的信心。

## 技术栈

- **前端**: Next.js 14 (App Router) + React + TypeScript
- **样式**: Tailwind CSS
- **AI SDK**: Vercel AI SDK（处理流式响应）
- **模型接口**: OpenAI 兼容格式（支持 OpenAI / vLLM / one-api 等）

## 核心功能

- ✅ 流式对话输出（打字机效果）
- ✅ 多轮对话上下文
- ✅ Markdown / 代码高亮渲染
- ✅ 清空对话
- ✅ 加载状态动画
- ✅ 响应式设计

## 快速开始

### 1. 安装依赖

```bash
cd 01-ai-chat-assistant
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.local
```

编辑 `.env.local`，填入你的 API Key：

```env
OPENAI_API_KEY=你的api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

> 💡 **也可以用本地部署的模型**：如果你已经用 vLLM 部署了开源模型，修改 `OPENAI_BASE_URL` 为你的 vLLM 地址即可。

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000 即可使用。

### 1. 流式输出原理
- 使用 `OpenAIStream` 将 SSE 流转换为可读流
- 前端通过 `useChat` hook 自动处理流式消息追加

### 2. 消息格式
- 标准的 OpenAI Chat Completions 格式：`{ role: 'user' | 'assistant' | 'system', content: string }`
- 每次请求都要带上完整的对话历史（这就是 Context）

### 3. Edge Runtime
- API 路由使用 `export const runtime = "edge"`，降低流式响应的延迟

## 可以扩展的方向

1. **多会话管理**：左侧加一个会话列表，用 localStorage 或后端存储
2. **系统提示词配置**：加一个设置面板，可以自定义 System Prompt
3. **模型切换**：支持切换不同的模型（GPT-3.5 / GPT-4 / 本地模型）
4. **消息复制 / 重生成**：单条消息的操作
5. **导出对话**：导出为 Markdown 或 JSON 文件

## 对应岗位要求

- ✅ LLM 应用开发基础
- ✅ Prompt 工程（可以通过扩展 System Prompt 来练习）
- ✅ Context 窗口理解
- ✅ Temperature 等参数调优
