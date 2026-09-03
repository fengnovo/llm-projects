
1.  __pycache__ 目录 它完全等价于前端的 node_modules/.cache！用于存储 Python 编译后的中间文件
2. venv 目录类似 前端的 node_modules，用于存储 Python 环境依赖
3. python3 -m venv venv 可以创建上面的 venv 目录，用于隔离 Python 环境 
4. 激活 venv 环境：source venv/bin/activate  类似前端的 nvm use 命令，会自动激活环境
5. 安装依赖：pip install -r requirements.txt 类似前端的 npm install 命令，会根据 requirements.txt 安装依赖
6. 运行项目：python app/main.py
7. 访问 http://localhost:8001/ 即可打开界面


__pycache__ 目录下的__init__.cpython-313.pyc 文件是 Python 编译后的字节码文件，用于存储 Python 类的元数据

| 片段 | 含义 | 前端类比 |
| --- | --- | --- |
| __init__ | 对应的源文件名（__init__.py） | 就是源文件的名字 |
| cpython | 解释器类型（标准 Python 就是用 C 写的 CPython） | 类似于“Chromium V8”引擎 |
| 313 | Python 版本号（3.13） | 相当于“Node v20.x” |
| .pyc | 编译后的字节码文件 | 类似于 .cache 或 .map 文件 |

.env 文件里的值优先级高于 config.py 里写的默认值。
```
class Config:
    env_file = ".env.example"   # 改完后，程序会去读 .env.example
```




## 项目清单汇总

| # | 项目名称 | 技术栈 | 核心能力 |
|---|----------|--------|---------|
| 1 | [AI 聊天助手](./01-ai-chat-assistant) | Next.js + TypeScript + Vercel AI SDK | LLM 调用、流式输出 |
| 2 | [AI 角色聊天引擎](./02-ai-character-engine) | FastAPI + LangChain + SQLite + Redis | 人设、记忆、情绪、Function Calling |
| 3 | [RAG 知识库问答](./03-rag-engine) | FastAPI + LangChain + ChromaDB | RAG 全流程、向量检索 |
| 4 | [Agent 任务助手](./04-agent-engine) | FastAPI + LangGraph | ReAct 模式、多工具调用、Agent 编排 |      
| 5 | [多模态内容推荐](./05-multimodal-engine) | FastAPI + CLIP + Qdrant | 图文检索、多模态 RAG |
| 6 | [模型网关与部署](./06-model-gateway-deployment) | LiteLLM + vLLM/Ollama + Redis | 模型抽象、限流降级灰度、私有化部署 |

---