from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.agent.engine import AgentExecutor


router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentRequest(BaseModel):
    query: str
    max_steps: Optional[int] = None


class AgentResponse(BaseModel):
    answer: str
    steps: List[Dict[str, Any]]
    total_steps: int


@router.post("/run", response_model=AgentResponse)
async def run_agent(req: AgentRequest):
    """
    运行 Agent（完整执行后返回结果）
    
    - **query**: 用户的问题或任务
    - **max_steps**: 最大迭代步数，防止死循环
    """
    try:
        executor = AgentExecutor()
        result = await executor.run(req.query, max_steps=req.max_steps)
        return AgentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")


@router.post("/stream")
async def stream_agent(req: AgentRequest):
    """
    流式运行 Agent（逐步返回执行过程）
    
    用 SSE 格式返回，每一步都是一个事件
    """
    try:
        from fastapi.responses import StreamingResponse
        import json
        
        executor = AgentExecutor()
        
        async def event_generator():
            # 注意：这里用同步的 stream，实际生产建议用异步
            # 简化处理：先完整执行再返回步骤
            result = await executor.run(req.query, max_steps=req.max_steps)
            
            # 逐步推送步骤
            for i, step in enumerate(result["steps"], 1):
                yield f"data: {json.dumps({'type': 'step', 'step': step}, ensure_ascii=False)}\n\n"
            
            # 最终答案
            yield f"data: {json.dumps({'type': 'final', 'answer': result['answer'], 'total_steps': result['total_steps']}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")


@router.get("/tools")
async def list_tools():
    """获取 Agent 可用的工具列表"""
    from app.agent.tools import ALL_TOOLS
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description.split('\n')[0].strip(),
                "args_schema": tool.args_schema.model_json_schema() if tool.args_schema else {},
            }
            for tool in ALL_TOOLS
        ]
    }
