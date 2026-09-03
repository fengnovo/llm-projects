> LLM 应用研发工程师
>
> 1. AI 角色引擎与 Agent 开发
> 负责 AI 虚拟角色的全链路对话逻辑：Prompt 工程、多轮长短期记忆机制（基于"事件簿"的自动总结，解决长对话中记忆丢失、车轱辘话、人设崩坏）、情绪与好感度状态机，打造高沉浸、高情商的 AI 伴侣。将业务能力封装为 Agent 工具（Function Calling），实现 AI 对话与计费、打赏、隐藏图集解锁等的无缝衔接，并保证工具调用的准确与容错。
> 2. 模型微调与人设优化
> 基于开源模型，使用 LoRA 等轻量级微调（SFT）结合自有聊天语料，持续优化模型的对话风格、人设稳定性与"不拒绝"能力（abliteration 去拒绝等）。沉淀私有微调模型，这是产品长期的核心竞争力。
> 3. 私域内容多模态 RAG 系统
> 将公司海量图文、视频及标签进行向量化（Embedding），结合多模态打标（如 Qwen-VL / CLIP 对封面、关键帧打标），构建多模态内容检索库。优化检索策略（混合检索、Rerank），让 AI 在与用户聊天时能结合语境"读懂空气"，精准且自然地推送相关媒体资源。
> 4. 开源模型部署与推理优化
> 负责开源大模型（Qwen3 等主流模型）的本地 / 云端 GPU 服务器私有化部署，使用 vLLM 等推理加速框架优化并发与响应速度，并建立有效的 Token 成本控制机制（Prompt 压缩、KV Cache 等）。
> 5. 模型网关与可扩展架构
> 搭建统一推理网关（LiteLLM / one-api 等）作为模型抽象层，使后续更换或新增模型（文本 / 图像 / 语音）只需调整配置而不影响上层业务；实现降级、限速、灰度，保证模型迭代不影响线上服务。
> 6. 后端接口对接
> 使用 Python（FastAPI / Flask）提供稳定高效的 AI 服务接口，与后端及前端团队协同完成产品快速迭代。
>
> 使用 FastAPI 或 Flask，熟悉 Redis、MySQL / PostgreSQL。
> 有真实落地的 LLM 应用（LLM Apps）开发经验：熟练 Agent 编排与 Function Calling、Prompt 工程，深刻理解 Context 窗口、Temperature、Top_p 等原理与调优。
> RAG 熟练工：熟悉主流向量数据库（Milvus、Qdrant、Chroma 等），有真实海量数据的 RAG 调优经验，了解如何解决幻觉与检索不准。
> 开源部署能力：熟悉 HuggingFace 生态，有使用 vLLM、Ollama 等在 Linux / GPU 环境部署开源大模型的实际经验（不依赖官方 API）。
> 掌握 LoRA 轻量级微调（SFT）的原理与流程，能用优质聊天数据反哺、优化模型表现。
> 极客精神与成本意识：关注开源 AI 社区动态，对算力成本敏感，懂得用工程化手段（Prompt 压缩、KV Cache 等）控制成本。
>
> 研究过或逆向过 AI 陪伴类产品（Character.AI、JanitorAI、星野、SillyTavern 酒馆等）。
> 有 Stable Diffusion（ComfyUI）图像生成，或开源 TTS（VITS、CosyVoice 等）语音生成的使用经验。
> 有模型 abliteration / 去拒绝相关的实践经验。

---
#### Python 后端基建
1. **Python 快速上手**
   - 有 TS 基础，Python 语法
   - 重点关注：类型提示（typing 模块）、异步（asyncio）、装饰器、上下文管理器
   - 推荐：Python 官方教程 + 刷 LeetCode 用 Python 写 20 道题

2. **FastAPI 深入**
   - 重点：路由、依赖注入（Depends）、Pydantic 数据校验、WebSocket（对话需要）、中间件
   - 实践：用 FastAPI 写一个简单的聊天接口，对接 OpenAI API，支持流式返回（SSE）

3. **Redis + MySQL 基础**
   - Redis：String / Hash / List / Sorted Set 基本操作、Pub/Sub、缓存策略
   - MySQL：基本 SQL、索引原理、连接池使用（SQLAlchemy / asyncpg）
   - 实践：给聊天接口加上对话历史存储（MySQL）+ 会话缓存（Redis）

一个基于 FastAPI 的流式聊天 API 服务，带对话历史持久化

---

#### 开源模型部署与推理
**部署开源大模型并优化推理**
1. **基础环境准备**
   - Linux 常用命令（ssh、scp、tmux、nvidia-smi、系统监控）
   - CUDA / cuDNN 基础概念（不需要精通，知道怎么装就行）
   - 云 GPU 平台：AutoDL、恒源云租一张 3090/4090，按小时付费，成本很低

2. **vLLM 部署实战**
   - 用 vLLM 部署 Qwen2.5-7B / Qwen3 系列模型
   - 掌握：OpenAI 兼容 API 模式、张量并行、连续批处理（continuous batching）
   - 理解：KV Cache 是什么、为什么能加速、显存怎么算

3. **推理优化实践**
   - 量化：GPTQ / AWQ / FP8 量化对速度和显存的影响
   - 测速：对比不同 batch size、并发数下的吞吐量和延迟
   - Prompt 压缩技巧：摘要、滑动窗口、重要信息置顶

4. **Ollama 辅助**
   - Ollama 更简单，可以先用来快速验证模型效果
   - 但重点还是 vLLM，因为要求的是生产级部署

一份部署文档 + 自己部署的 vLLM 推理服务（OpenAI 兼容接口），附上性能测试报告

---

#### 角色引擎核心

**独立设计并实现一个 AI 虚拟角色的对话系统**
1. **Prompt 工程进阶**
   - 角色 Prompt 的经典结构：人设 + 说话风格 + 背景故事 + 对话示例（few-shot）+ 行为约束
   - 研究 Character.AI / JanitorAI / 星野 的 Prompt 设计思路（去 Reddit、GitHub 上搜别人逆向出来的结果）
   - 实践：为一个角色写一份高质量的 System Prompt，测试不同 Temperature / Top_p 下的表现

2. **记忆系统设计**
   - **短期记忆**：最近 N 轮对话（滑动窗口）
   - **长期记忆**：基于"事件簿"的自动总结机制
     - 每 M 轮对话触发一次总结，提取关键事件、用户信息、关系变化
     - 总结结果结构化存储（可以用 JSON 存在 MySQL，也可以向量化后检索）
   - 记忆检索：对话时从长期记忆中召回相关信息注入 Context
   - 实践：实现一个简单的记忆模块，测试 50 轮以上长对话的记忆保持效果

3. **情绪与好感度状态机**
   - 设计情绪状态模型（比如：开心 / 平静 / 害羞 / 生气 / 悲伤，多维数值表示）
   - 设计好感度等级系统
   - 对话中根据用户输入和回复内容更新状态
   - 状态影响回复风格的 Prompt 注入
   - 实践：用状态机模式实现一个情绪系统，接入对话流程

4. **Function Calling 与容错**
   - 用 LangGraph 工具调用
   - 重点：工具调用的**可靠性保障**——重试、参数校验、失败降级、结果注入格式
   - 实践：实现"查询用户余额"、"解锁图集"两个模拟工具，处理各种异常情况

一个完整的角色引擎原型（人设 + 记忆 + 情绪 + Function Calling），可以是一个 FastAPI 服务

---

#### RAG 加深 + 多模态

**从文本 RAG 升级到多模态 RAG**
1. **向量数据库深入**
   - 选 Milvus 或 Qdrant 
   - 理解：索引类型（HNSW / IVF）、相似度度量、过滤检索、批量插入优化
   - 实践：搭建一个百万级向量的检索服务，测召回率和延迟

2. **RAG 调优实战**
   - 混合检索：关键词检索（BM25）+ 向量检索的融合（比如用 RRF 算法）
   - Rerank：用 BGE-Reranker / Cohere Rerank 对初筛结果重排序
   - 幻觉缓解：引用溯源、答案校验、"不知道就说不知道"的 Prompt 设计

3. **多模态 RAG**
   - 图像向量化：CLIP / Qwen-VL / 多模态 Embedding 模型
   - 视频处理：关键帧提取（ffmpeg）+ 帧向量化 + 时序信息保留
   - 实践：把一批图片 / 视频封面向量化，实现"根据对话内容推荐相关图片"的功能

4. **标签体系设计**
   - 如何用 LLM / VLM 给内容自动打标签
   - 标签 + 向量的混合检索策略

一个多模态内容检索服务，支持图文混合检索，接入角色引擎实现"聊天时自然推图"

---

#### 微调与模型优化

**LoRA 微调全流程，能独立完成一次微调实验**
"掌握原理与流程"，不需要是算法专家，但得亲手做过。

1. **理论基础**
   - LoRA / QLoRA 的原理（低秩适配，为什么能省显存）
   - SFT（监督微调）的基本流程
   - 数据集格式：ShareGPT / Alpaca 等常见格式

2. **动手微调**
   - 用 LLaMA-Factory 或 unsloth 框架
   - 准备 1k~10k 条角色对话数据（可以用 GPT-4 生成一批 synthetic data）
   - 在 3090/4090 上微调一个 7B 模型的 LoRA
   - 评估微调效果：人设一致性、说话风格、拒绝率

3. **abliteration / 去拒绝**
   - 了解概念：通过修改模型权重或微调来减少模型的安全拒绝
   - 可以读几篇相关论文 / GitHub 项目了解方法
   - 实践上可以用微调数据引导（加入更多"不拒绝"的对话样本）

一个微调过的角色 LoRA 权重 + 微调实验报告（数据、参数、效果对比）

---

#### 模型网关与架构

**模型抽象层的设计思路**

1. **LiteLLM / one-api**
   - 部署一个 one-api 或 LiteLLM 网关
   - 接入多个模型供应商（OpenAI + 自己的 vLLM 服务）
   - 配置路由、负载均衡、降级策略

2. **生产级能力**
   - 限流：Token 级 / 请求级限流（Redis 实现）
   - 灰度：按用户 / 比例切流到新模型
   - 监控：Token 用量统计、成功率、延迟监控

一个模型网关配置方案 + 架构图

---

#### 项目：AI 虚拟角色聊天应用

**项目架构：**
```
前端
    ↓
FastAPI 后端服务
    ↓
角色引擎（Prompt + 记忆 + 情绪 + Function Calling）
    ↓
模型网关（LiteLLM）→ vLLM 部署的开源模型
    ↓
多模态 RAG 服务（Qdrant + CLIP + Rerank）
```

**核心功能清单：**
1. 用户可以和 AI 角色聊天，支持流式回复
2. 角色有稳定人设、记忆用户说过的话（长短期记忆）
3. 有好感度 / 情绪系统，影响回复风格
4. 聊天中会根据语境推荐相关图片（多模态 RAG）
5. 有"解锁隐藏图集"的 Function Calling 演示
6. 后台有 Token 用量统计和对话日志

**技术栈建议：**
- 后端：FastAPI + SQLAlchemy + Redis + Qdrant
- 模型部署：vLLM + Qwen2.5-7B（或更小的模型先跑通）
- RAG：BGE Embedding + BGE-Reranker + CLIP（图像）
- 微调：LLaMA-Factory（可选，做一个角色 LoRA）
- 前端：React / Vue


| 方向 | 资源 |
|------|------|
| FastAPI | 官方文档 + FastAPI 高手课 |
| vLLM | 官方文档 + GitHub README 里的 examples |
| 角色引擎 | GitHub 搜 `SillyTavern`、`RisuAI`，研究它们的 Prompt 模板和记忆系统设计 |
| RAG | LangChain 官方文档 + RAG 技术栈详解 |
| 微调 | LLaMA-Factory 文档 + B 站搜"LoRA 微调" |
| 多模态 | Qwen-VL 官方文档 + CLIP 相关教程 |

```
Python + FastAPI + Redis/MySQL → 写出第一个聊天 API
vLLM 部署 + 推理优化 → 自己的模型能跑起来
角色引擎核心（Prompt + 记忆 + 情绪 + 工具调用）→ 核心竞争力
多模态 RAG → 补全 RAG 深度
微调 + 模型网关 → 加分项 + 架构视野
```
#### 项目 1：AI 聊天助手（带流式输出）
**核心功能：**
- 流式对话（SSE）
- 对话历史存储（localStorage + 后端持久化）
- 多会话切换
- Markdown 渲染 + 代码高亮

**技术栈：**
- 前端：React + Vite + shadcn/ui
- 后端：Next.js API Routes / Express.js（Node.js）
- AI SDK：Vercel AI SDK 或 LangChain.js

**推荐模板：**
- Vercel AI SDK Chatbot — 官方示例，Next.js + LangChain.js，流式开箱即用
- chatgpt-web — Vue3 + Express，中文社区热门，代码好读

**目标：**
- 理解流式输出的实现原理（SSE / Fetch ReadableStream）
- 掌握 LLM API 的调用方式和参数调优
- 体验从前端到 AI 的完整链路

---

#### 项目 2：知识库 RAG 问答
**核心功能：**
- 上传 PDF / Markdown 文档
- 文档切片 + 向量化
- 基于文档的问答
- 引用来源展示

**技术栈：**
- 前端：React + Tailwind
- 后端：Next.js / Express
- 向量库：ChromaDB（JS 支持好，轻量，本地就能跑）
- AI：LangChain.js + OpenAI API

**推荐模板：**
- langchainjs-retrieval-agent — LangChain 官方示例
- Quivr — 开源的"第二大脑"RAG 项目，TS 全栈，可以直接看源码
- notion-qa — 简洁的 RAG 入门项目

**目标：**
- 搞懂 RAG 全流程：加载 → 切片 → 向量化 → 检索 → 生成
- 理解 Embedding、相似度检索的基本概念
- 踩坑：文档切片策略、检索准确率优化

---
#### 项目 3：AI 角色聊天引擎
**核心功能：**
- 角色人设系统（System Prompt 配置化）
- 短期记忆（滑动窗口）+ 长期记忆（自动总结的事件簿）
- 好感度 / 情绪状态机
- Function Calling 工具调用（比如"查询天气"、"播放音乐"）
- 聊天界面

**技术栈：**
- 前端：React / Vue
- 后端：FastAPI（Python）+ LangChain Python
- 数据库：MySQL / PostgreSQL（存对话、记忆）+ Redis（缓存）
- 模型：先用 OpenAI API，后面换成 vLLM 部署的开源模型

**推荐模板 / 参考项目：**
- SillyTavern — AI 角色扮演界的"事实标准"，Node.js 写的，研究它的 Prompt 模板、记忆系统、角色卡格式
- RisuAI — 另一个优秀的角色聊天前端，TS 写的，代码质量高
- characterai-node — 逆向 Character.AI 的库，可以参考它的 API 设计思路
- LangChain 对话记忆文档 — 官方文档，讲了各种记忆方案

**前端可以参考的 UI：**
- 星野、筑梦岛、Character.AI 的 UI 设计
- 做一个左右分栏：左边角色列表，右边聊天窗口

**目标：**
- 掌握角色 Prompt 工程的精髓
- 独立设计并实现记忆系统
- 理解状态机在情绪系统中的应用
- 会用 FastAPI 写 AI 服务

---

#### 项目 4：Agent 任务助手
**核心功能：**
- 多工具调用（搜索、计算器、数据库查询、代码执行）
- 任务规划与拆解
- 多轮推理（ReAct 模式）
- 工具调用结果可视化

**技术栈：**
- 前端：React 做一个 Agent 工作台（展示思考过程、工具调用日志）
- 后端：LangGraph（Python 或 JS 都行，推荐 Python 版更成熟）
- 工具：Tavily（搜索）+ 自定义工具

**推荐模板：**
- LangGraph 官方示例 — 大量 Agent 示例，从简单到复杂
- langgraphjs-starter — JS 版，前端友好
- GPT Engineer — 代码生成 Agent，可以参考它的 Agent 架构
- Open Interpreter — 本地代码执行 Agent，Python 写的，值得研究

**目标：**
- 掌握 ReAct、Plan-and-Execute 等 Agent 模式
- 会用 LangGraph 编排复杂的状态流
- 理解工具调用的可靠性设计（重试、参数校验、错误处理）

---
#### 项目 5：多模态内容推荐系统
**核心功能：**
- 上传图片 / 视频，自动打标签 + 向量化
- 聊天时根据语境推荐相关图片
- 标签 + 向量混合检索
- 推荐结果展示（瀑布流 / 卡片）

**技术栈：**
- 前端：React + 图片瀑布流组件
- 后端：FastAPI + Milvus / Qdrant
- 多模态模型：CLIP（图文向量）+ Qwen-VL（图像描述 / 打标签）
- 视频处理：ffmpeg 抽关键帧

**推荐模板 / 参考：**
- Qdrant 多模态搜索示例 — 官方 demo，有 CLIP 图文检索示例
- Towhee — 多模态向量处理框架，Python 写的，封装了大量模型
- img2vec — 图像向量化的简洁实现
- Video-RAG — 视频 RAG 的参考实现

**目标：**
- 理解多模态 Embedding 的原理
- 掌握图文混合检索的实现方式
- 会处理视频等非结构化数据

---
#### 项目 6：私有化模型部署 + 模型网关
**核心功能：**
- 用 vLLM 部署一个开源大模型（比如 Qwen2.5-7B）
- 搭建模型网关（one-api 或 LiteLLM）
- 实现多模型路由 + 限流 + 降级
- 监控面板（Token 用量、延迟、成功率）

**技术栈：**
- 部署：vLLM + Docker + Linux
- 网关：one-api（Go 写的，但部署简单，界面友好）或 LiteLLM Proxy（Python）
- 监控：Prometheus + Grafana（可选，先做简单的统计）

**推荐模板 / 参考：**
- vLLM 官方部署文档 — OpenAI 兼容服务，一键启动
- one-api — 大模型 API 管理系统，中文项目，部署简单，功能齐全
- LiteLLM Proxy — Python 写的模型网关，和 LangChain 生态集成好
- Ollama WebUI — Ollama 的 Web 界面，可以参考它的架构

**目标：**
- 掌握开源大模型的部署流程
- 理解推理加速的基本原理（vLLM 的 PagedAttention 等）
- 会模型网关的架构设计思想

---

### 终极项目：完整的 AI 虚拟角色产品
**项目架构图：**
```
┌─────────────────────────────────────────┐
│           前端（React / Vue）           │
│  聊天界面 + 角色广场 + 个人中心         │
└──────────────────┬──────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────┐
│           FastAPI 后端服务              │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 角色引擎  │ │  RAG 服务 │ │ 用户系统│ │
│  │(记忆/情绪)│ │(多模态)   │ │         │ │
│  └────┬─────┘ └────┬─────┘ └────┬────┘ │
└───────┼─────────────┼────────────┼──────┘
        │             │            │
┌───────▼─────────────▼────────────▼──────┐
│           模型网关（LiteLLM）            │
│     路由 / 限流 / 降级 / 监控            │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         vLLM 推理集群（开源模型）        │
│    Qwen3 / 其他开源模型 + LoRA 权重      │
└─────────────────────────────────────────┘
```

**分阶段：**
1. 前端 + FastAPI + 角色引擎 + 调用 OpenAI API
2. 加入记忆系统 + RAG 推荐 + 模型网关
3. 接入 vLLM 私有化部署 + LoRA 微调模型

---

## 第三部分：项目创建与打包
### 项目总览

| 项目 | 路径 | 难度 | 对应能力 |
|------|------|------|-------------|
| **AI 聊天助手** | `01-ai-chat-assistant/` | ⭐ | LLM 应用基础、流式输出 |
| **AI 角色聊天引擎**（核心） | `02-ai-character-engine/` | ⭐⭐⭐ | 人设、记忆系统、情绪状态机、Function Calling、FastAPI |
| **RAG 知识库问答** | `03-rag-knowledge-base/` | ⭐⭐ | RAG 全流程、向量数据库、文档处理 |

---

### 快速运行指南

#### 项目 1：AI 聊天助手

```bash
cd 01-ai-chat-assistant
npm install
cp .env.example .env.local 
npm run dev
# 访问 http://localhost:3000
```

#### 项目 2：AI 角色聊天引擎

```bash
# 后端
cd 02-ai-character-engine/backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     
python -m app.main
# 后端运行在 http://localhost:8000
# API 文档：http://localhost:8000/docs

# 前端（直接打开，不用构建）
# 用浏览器打开 02-ai-character-engine/frontend/index.html
```

#### 项目 3：RAG 知识库问答

```bash
# 后端
cd 03-rag-knowledge-base/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      
python -m app.main
# 后端运行在 http://localhost:8001

# 前端
# 用浏览器打开 03-rag-knowledge-base/frontend/index.html
# 上传 sample_docs/ 目录下的 .md 文件测试
```

```
项目 1（聊天助手）→ 熟悉 LLM 调用、流式输出
      ↓
项目 3（RAG 知识库）→ 掌握 RAG 全流程、向量数据库
      ↓
项目 2（角色引擎）→ 核心！整合记忆、情绪、Agent 工具调用
```
---

### 项目总览

| # | 项目 | 路径 | 难度 | 核心能力 |
|---|------|------|------|---------|
| 1 | AI 聊天助手 | `01-ai-chat-assistant/` | ⭐ | LLM 调用、流式输出、Next.js 全栈 |
| 2 | **AI 角色聊天引擎**（核心） | `02-ai-character-engine/` | ⭐⭐⭐ | 人设、长短期记忆、情绪状态机、Function Calling |
| 3 | RAG 知识库问答 | `03-rag-knowledge-base/` | ⭐⭐ | RAG 全流程、ChromaDB、文档切片 |
| 4 | Agent 任务助手 | `04-agent-task-assistant/` | ⭐⭐⭐ | LangGraph、ReAct 模式、多工具调用 |
| 5 | 多模态内容推荐 | `05-multimodal-rag/` | ⭐⭐⭐⭐ | CLIP、图文统一向量空间、Qdrant、混合检索 |

```
项目 1（聊天助手）→ 熟悉 LLM 调用和流式输出
    ↓
项目 3（RAG 知识库）→ 掌握 RAG 全流程和向量数据库
    ↓
项目 4（Agent 助手）→ 理解 ReAct 模式和 LangGraph 状态流
    ↓
项目 2（角色引擎）→ 核心！整合记忆、情绪、人设、工具调用
    ↓
项目 5（多模态推荐）→ 高级！多模态 RAG + 内容推荐
```
---

### 快速运行

每个项目都有独立的 `README.md`，包含详细的启动说明和原理讲解。

```bash
# 项目 1（Next.js）
cd 01-ai-chat-assistant && npm install && npm run dev

# 项目 2/3/4/5（Python FastAPI）
cd 项目目录/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入 API Key
python -m app.main

# 前端：直接打开对应项目的 frontend/index.html
```

创建了项目 6：私有化模型部署 + 模型网关，包含：
- LiteLLM 网关配置 + Docker Compose 一键启动
- vLLM 部署脚本和文档
- Ollama 部署脚本和文档
- Mock LLM 服务（无 GPU 演示用）
- 网关中间件（限流、降级、灰度、计费）
- 监控面板前端
- 示例客户端、压测脚本、成本计算器
- 架构设计文档
