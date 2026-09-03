"""
文档处理模块

支持的文档格式：
- .txt 纯文本
- .md Markdown
- .pdf PDF 文件

功能：
- 文档加载
- 文本切片（分块）
"""
import os
from typing import List
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


class DocumentProcessor:
    """文档处理器"""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )

    def load_file(self, file_path: str, filename: str) -> str:
        """加载文件内容"""
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            return self._load_pdf(file_path)
        elif ext in [".txt", ".md", ".markdown"]:
            return self._load_text(file_path)
        else:
            # 默认按文本处理
            return self._load_text(file_path)

    def _load_text(self, file_path: str) -> str:
        """加载文本文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_pdf(self, file_path: str) -> str:
        """加载 PDF 文件"""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        return text

    def split_text(self, text: str, source: str = "") -> List[dict]:
        """
        将文本切片
        
        返回：
        [
            {"content": "片段内容", "metadata": {"source": "来源", "chunk_index": 0}},
            ...
        ]
        """
        chunks = self.text_splitter.split_text(text)
        return [
            {
                "content": chunk,
                "metadata": {
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]

    def process_file(self, file_path: str, filename: str) -> List[dict]:
        """处理单个文件（加载 + 切片）"""
        text = self.load_file(file_path, filename)
        return self.split_text(text, source=filename)
