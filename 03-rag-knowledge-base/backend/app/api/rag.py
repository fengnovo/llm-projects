import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from app.rag_engine import RAGEngine
from app.document_processor import DocumentProcessor
from app.vectorstore import get_vector_store


router = APIRouter(prefix="/api/rag", tags=["rag"])

# 临时上传目录
UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QueryRequest(BaseModel):
    question: str
    k: Optional[int] = None  # 检索数量


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    retrieved_docs: List[dict]


@router.post("/query", response_model=QueryResponse)
async def query_rag(req: QueryRequest):
    """RAG 查询（非流式）"""
    try:
        engine = RAGEngine()
        result = await engine.query(req.question, k=req.k)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_rag_stream(req: QueryRequest):
    """RAG 查询（流式）"""
    try:
        engine = RAGEngine()

        async def event_generator():
            async for chunk in engine.query_stream(req.question, k=req.k):
                yield f"data: {chunk}\n\n"
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    上传文档到知识库
    
    支持格式：.txt, .md, .pdf
    可以一次上传多个文件
    """
    try:
        processor = DocumentProcessor()
        vector_store = get_vector_store()

        total_chunks = 0
        uploaded_files = []

        for file in files:
            # 保存临时文件
            file_id = str(uuid.uuid4())
            file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # 处理文档
            chunks = processor.process_file(file_path, file.filename)

            # 添加到向量库
            texts = [c["content"] for c in chunks]
            metas = [c["metadata"] for c in chunks]
            ids = [f"{file_id}_{i}" for i in range(len(chunks))]

            vector_store.add_documents(texts, metas, ids)

            total_chunks += len(chunks)
            uploaded_files.append({
                "filename": file.filename,
                "chunks": len(chunks),
            })

            # 清理临时文件
            os.remove(file_path)

        stats = vector_store.get_collection_stats()

        return {
            "success": True,
            "message": f"成功上传 {len(uploaded_files)} 个文件，共 {total_chunks} 个片段",
            "uploaded_files": uploaded_files,
            "total_documents": stats["document_count"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/add-text")
async def add_text(content: str, source: str = "manual"):
    """直接添加文本到知识库"""
    try:
        engine = RAGEngine()
        ids = await engine.add_document(content, {"source": source})
        return {
            "success": True,
            "message": f"成功添加，共 {len(ids)} 个片段",
            "chunk_count": len(ids),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """获取知识库统计信息"""
    try:
        engine = RAGEngine()
        return engine.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_knowledge_base():
    """清空知识库（谨慎使用）"""
    try:
        vector_store = get_vector_store()
        vector_store.delete_collection()
        return {"success": True, "message": "知识库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
