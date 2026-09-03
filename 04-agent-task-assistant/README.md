# 项目 4：Agent 任务助手

> 进阶级项目 · LangGraph + ReAct 模式 + 多工具调用

## 项目简介

一个基于 LangGraph 的智能 Agent，采用 ReAct（推理 + 行动）模式，能够自主思考、选择工具、执行操作，一步步解决复杂问题。

## 技术栈

- **LangGraph**：Agent 状态流编排（循环、分支、持久化）
- **LangChain**：工具封装、消息抽象
- **FastAPI**：Web 服务
- **OpenAI 兼容模型**：需要支持 Function Calling

## 核心功能

- ✅ ReAct 模式（思考 → 行动 → 观察 → 循环）
- ✅ 5 个内置工具（计算器、搜索、时间、代码执行、翻译）
- ✅ LangGraph 状态图管理
- ✅ 最大步数限制（防止死循环）
- ✅ 执行步骤可视化
- ✅ 可扩展的工具系统

## 快速开始

```bash
cd 04-agent-task-assistant/backend

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # 填入 API Key
python -m app.main
```

- 后端：http://localhost:8002
- API 文档：http://localhost:8002/docs
- 前端：直接打开 `frontend/index.html`

## 可以测试的问题

1. **数学计算**：`计算 1234 * 5678 的结果`
2. **时间查询**：`现在几点了？今天星期几？`
3. **联网搜索**：`搜索一下 LangChain 是什么`
4. **翻译**：`把 Hello World 翻译成中文`
5. **代码执行**：`用 Python 写一个斐波那契函数并测试前 10 项`
6. **多步任务**：`现在是星期几？再计算从 1 加到 100 的和`

## 核心概念

### ReAct 模式

ReAct = Reasoning + Acting（推理 + 行动）

```
用户问题
  ↓
Thought（思考）：我需要做什么？
  ↓
Action（行动）：调用某个工具
  ↓
Observation（观察）：工具返回结果
  ↓
Thought（再思考）：结果够不够？还要做什么？
  ↓
... 循环 ...
  ↓
Final Answer（最终答案）
```

### LangGraph 状态图

为什么用 LangGraph 而不是普通的 Chain？

- **支持循环**：Agent 可以反复调用工具（Chain 是线性的）
- **支持分支**：根据条件走不同路径
- **状态管理**：每一步的状态都在图中流动
- **可持久化**：可以保存和恢复 Agent 的状态

本项目的图结构：

```
      ┌─────┐
      │start│
      └──┬──┘
         ▼
      ┌───────┐
      │ agent │ ←──────────┐
      └───┬───┘            │
          │                │
    ┌─────┴─────┐          │
    │  判断下一步 │          │
    └─────┬─────┘          │
          │                │
    ┌─────┴─────┐     ┌────┴────┐
    │   tools   │────→│    END  │
    └───────────┘     └─────────┘
```

### 工具系统

每个工具是一个 `@tool` 装饰的函数，包含：
- 名称（name）
- 描述（description）→ 告诉模型这个工具是做什么的
- 参数 Schema（args_schema）→ 告诉模型需要传什么参数

**关键技巧**：工具的描述写得越清楚，模型调用越准确。

## 扩展方向

### 1. 加入更多工具
- 数据库查询工具
- API 调用工具
- 文件读写工具
- 邮件发送工具
- 网页抓取工具

### 2. 多 Agent 协作
- 规划 Agent + 执行 Agent
- 专家团队（不同领域的 Agent 协作）
- Supervisor 模式（一个 Agent 管理其他 Agent）

### 3. 记忆系统
- 短期记忆（对话历史）
- 长期记忆（向量数据库存储的经验）

### 4. 人工介入
- 关键步骤需要人确认
- 工具调用前的审批

## 对应岗位要求

- ✅ Agent 编排
- ✅ Function Calling
- ✅ 工具调用的准确性与容错
- ✅ LangChain / LangGraph 实战经验

## 面试怎么说

> "我用 LangGraph 实现了一个 ReAct 模式的 Agent，支持多工具调用。
> 我设计了 5 个工具（计算器、搜索、时间、代码执行、翻译），
> Agent 可以根据问题自主选择工具，最多支持 N 步迭代，并有防止死循环的机制。
> 我还做了执行步骤的可视化，可以清晰看到 Agent 的思考过程。"
