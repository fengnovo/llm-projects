# LangChain 入门指南

LangChain 是一个用于开发大语言模型应用的框架，它提供了一系列工具和组件，让你可以快速构建复杂的 LLM 应用。

## 核心概念

### 1. Model（模型）
LangChain 封装了各种 LLM 供应商，包括 OpenAI、Anthropic、本地模型等。
你可以用统一的接口调用不同的模型。

### 2. Prompt（提示词）
Prompt 模板可以让你动态构建提示词，支持变量替换。

### 3. Chain（链）
Chain 是 LangChain 的核心概念，它把多个步骤串联起来。
比如：Prompt 模板 → 模型调用 → 输出解析，这就是一个链。

### 4. Agent（智能体）
Agent 可以根据用户的问题，自主决定调用哪些工具来解决问题。
它比 Chain 更灵活，适合复杂的多步推理任务。

### 5. Memory（记忆）
Memory 让对话系统能够记住历史消息，支持多轮对话。

### 6. Retriever（检索器）
Retriever 用于从外部数据源检索相关信息，是 RAG 系统的核心组件。

## 为什么用 LangChain？

1. **生态丰富**：集成了上百种模型、向量库、工具
2. **组件化**：各个模块可以灵活组合
3. **减少重复代码**：常用功能都封装好了
4. **社区活跃**：更新快，问题容易找到答案

## LangChain vs LangGraph

LangGraph 是 LangChain 的扩展，专注于构建有状态的、多角色的 Agent 应用。
- LangChain 适合线性流程（Chain）
- LangGraph 适合循环、分支、状态管理的复杂 Agent

## 快速上手示例

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. 初始化模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 2. 创建 Prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，请用{style}的风格回答问题。"),
    ("user", "{question}")
])

# 3. 构建链
chain = prompt | llm | StrOutputParser()

# 4. 调用
result = chain.invoke({
    "role": "Python 专家",
    "style": "简洁明了",
    "question": "什么是装饰器？"
})

print(result)
```
