"""
Agent 核心 - 基于 LangGraph 的 ReAct Agent

ReAct 模式：Reasoning + Acting（推理 + 行动）
- 模型先思考（Thought）：我需要做什么？
- 然后决定行动（Action）：调用哪个工具，参数是什么
- 观察结果（Observation）：工具返回了什么
- 循环直到得出最终答案

LangGraph 用来管理状态流，支持循环、分支、持久化。
"""
import json
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
import operator

from app.config import settings
from app.agent.tools import ALL_TOOLS


# ========== Agent 状态定义 ==========
class AgentState(TypedDict):
    """Agent 的状态，在图的节点之间传递"""
    messages: Annotated[List[BaseMessage], operator.add]  # 对话历史
    steps: List[Dict[str, Any]]  # 执行步骤记录
    current_step: int  # 当前步数
    max_steps: int  # 最大步数


# ========== 系统提示词 ==========
SYSTEM_PROMPT = """
你是一个智能任务助手，能够使用各种工具来帮助用户解决问题。

【工作方式】
你需要通过"思考-行动-观察"的循环来解决问题：
1. Thought（思考）：分析用户的问题，决定下一步该做什么
2. Action（行动）：选择合适的工具并调用
3. Observation（观察）：查看工具返回的结果
4. 重复以上步骤，直到你能给出最终答案

【工具使用规则】
- 可以多次调用工具，也可以调用不同的工具
- 如果一个工具不够，可以组合使用多个工具
- 不要猜测答案，不确定的就搜索或计算
- 如果尝试了几次都失败，可以向用户说明

【回答风格】
- 最终回答要清晰、有条理
- 如果用到了工具，可以简要说明你做了什么
- 用中文回答

【可用工具】
{tool_descriptions}
"""


# ========== 初始化 LLM 和工具 ==========
def get_llm():
    """获取 LLM 实例"""
    return ChatOpenAI(
        model=settings.AGENT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=0,
        max_tokens=1000,
    ).bind_tools(ALL_TOOLS)


# ========== 图节点函数 ==========
def agent_node(state: AgentState) -> Dict:
    """
    Agent 推理节点
    
    接收当前状态（消息列表），调用 LLM，返回下一步动作
    """
    llm = get_llm()
    
    # 构建消息：系统提示 + 历史消息
    tool_descriptions = "\n".join([
        f"- {tool.name}: {tool.description}"
        for tool in ALL_TOOLS
    ])
    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(tool_descriptions=tool_descriptions))
    
    messages = [system_msg] + state["messages"]
    
    # 调用 LLM
    response = llm.invoke(messages)
    
    return {
        "messages": [response],
        "steps": state.get("steps", []),
        "current_step": state.get("current_step", 0) + 1,
        "max_steps": state.get("max_steps", settings.MAX_AGENT_STEPS),
    }


def tool_node(state: AgentState) -> Dict:
    """
    工具执行节点
    
    执行模型要求的工具调用，返回结果
    """
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {"messages": [], "steps": state.get("steps", [])}
    
    steps = state.get("steps", [])
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        # langchain-core 0.2+ 中 tool_calls 元素为 dict：{'name', 'args', 'id'}
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call.get("id")
        
        # 查找工具
        tool_obj = next((t for t in ALL_TOOLS if t.name == tool_name), None)
        
        if tool_obj:
            try:
                # 执行工具
                result = tool_obj.invoke(tool_args)
                result_str = json.dumps(result, ensure_ascii=False, indent=2)
            except Exception as e:
                result_str = f"工具执行出错: {str(e)}"
                result = {"success": False, "error": str(e)}
        else:
            result_str = f"工具 {tool_name} 不存在"
            result = {"success": False, "error": f"工具 {tool_name} 不存在"}
        
        # 记录步骤
        steps.append({
            "step": len(steps) + 1,
            "type": "tool_call",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "result": result,
        })
        
        tool_messages.append(ToolMessage(
            content=result_str,
            tool_call_id=tool_id,
        ))
    
    return {
        "messages": tool_messages,
        "steps": steps,
    }


# ========== 条件边：判断是否继续 ==========
def should_continue(state: AgentState) -> str:
    """
    判断 Agent 是否需要继续行动
    
    返回：
    - "tools"：继续调用工具
    - "end"：结束，返回最终答案
    """
    last_message = state["messages"][-1]
    current_step = state.get("current_step", 0)
    max_steps = state.get("max_steps", settings.MAX_AGENT_STEPS)
    
    # 超过最大步数，强制结束
    if current_step >= max_steps:
        return "end"
    
    # 如果 LLM 要调用工具，继续
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # 否则结束
    return "end"


# ========== 构建 LangGraph 图 ==========
def build_agent_graph():
    """
    构建 Agent 的状态图
    
    流程：
    agent → （判断） → tools → agent → （判断） → ... → end
    """
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # 设置入口
    workflow.set_entry_point("agent")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )
    
    # 工具执行完后回到 agent
    workflow.add_edge("tools", "agent")
    
    # 编译图
    return workflow.compile()


# ========== Agent 执行器 ==========
class AgentExecutor:
    """Agent 执行器，封装图的运行逻辑"""
    
    def __init__(self):
        self.graph = build_agent_graph()
    
    async def run(self, query: str, max_steps: int = None) -> Dict[str, Any]:
        """
        运行 Agent，处理用户查询
        
        返回：
        {
            "answer": "最终回答",
            "steps": [...],  // 执行步骤
            "total_steps": N,
        }
        """
        max_steps = max_steps or settings.MAX_AGENT_STEPS
        
        # 初始状态
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "steps": [],
            "current_step": 0,
            "max_steps": max_steps,
        }
        
        # 运行图
        result = await self.graph.ainvoke(initial_state)
        
        # 提取最终回答（最后一条 AI 消息）
        final_answer = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                final_answer = msg.content
                break
        
        return {
            "answer": final_answer,
            "steps": result["steps"],
            "total_steps": len(result["steps"]),
            "intermediate_messages": [
                {
                    "role": msg.type,
                    "content": msg.content,
                    "tool_calls": getattr(msg, 'tool_calls', None),
                }
                for msg in result["messages"]
            ],
        }
    
    def stream(self, query: str, max_steps: int = None):
        """流式运行（逐步输出）"""
        max_steps = max_steps or settings.MAX_AGENT_STEPS
        
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "steps": [],
            "current_step": 0,
            "max_steps": max_steps,
        }
        
        # 流式输出图的执行过程
        for event in self.graph.stream(initial_state):
            yield event
