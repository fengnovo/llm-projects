"""
Agent 工具定义

每个工具是一个独立的函数，Agent 可以根据用户问题自主选择调用。

工具列表：
1. calculator - 数学计算器
2. web_search - 联网搜索（模拟/真实）
3. get_current_time - 获取当前时间
4. code_executor - Python 代码执行（沙箱模拟）
5. translate - 翻译工具
"""
import re
import math
import datetime
from typing import Dict, Any, List
from langchain_core.tools import tool


# ========== 工具 1：计算器 ==========
@tool
def calculator(expression: str) -> Dict[str, Any]:
    """
    数学计算器。当你需要进行数学计算时使用。
    支持加减乘除、括号、幂运算、常用函数（sin, cos, sqrt 等）。
    
    参数:
        expression: 数学表达式字符串，例如 "2 + 3 * 4"、"sqrt(16)"、"sin(pi/2)"
    """
    try:
        # 安全的数学计算环境
        safe_dict = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'pow': pow,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'sqrt': math.sqrt, 'exp': math.exp, 'log': math.log,
            'log10': math.log10, 'log2': math.log2,
            'pi': math.pi, 'e': math.e,
        }
        
        # 只允许数学相关的字符
        if not re.match(r'^[\d\s+\-*/().,%\w]+$', expression):
            return {"success": False, "error": "表达式包含非法字符"}
        
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        return {
            "success": True,
            "expression": expression,
            "result": result,
        }
    except Exception as e:
        return {"success": False, "error": f"计算错误: {str(e)}"}


# ========== 工具 2：联网搜索 ==========
@tool
def web_search(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    联网搜索。当你需要查询实时信息、最新动态、或者不知道的知识时使用。
    
    参数:
        query: 搜索关键词
        num_results: 返回结果数量，默认 3 条
    """
    # 如果配置了 Tavily API Key，调用真实搜索
    # 这里为了演示，返回模拟数据
    mock_results = {
        "今天天气": [
            {"title": "今日天气预报", "content": "北京今日晴转多云，气温 22-28°C，空气质量优，适合户外活动。", "url": "https://example.com/weather"},
            {"title": "本周天气趋势", "content": "本周天气以晴为主，周末有小雨，气温在 20-30°C 之间。", "url": "https://example.com/weekly"},
        ],
        "python": [
            {"title": "Python 官方网站", "content": "Python 是一种解释型、面向对象、动态数据类型的高级程序设计语言。最新版本 Python 3.12。", "url": "https://python.org"},
            {"title": "Python 应用领域", "content": "Python 广泛应用于 Web 开发、数据分析、人工智能、科学计算、自动化运维等领域。", "url": "https://example.com/python"},
        ],
        "langchain": [
            {"title": "LangChain 简介", "content": "LangChain 是一个用于开发大语言模型应用的框架，提供了 Chain、Agent、Memory 等核心概念。", "url": "https://langchain.com"},
            {"title": "LangGraph", "content": "LangGraph 是 LangChain 的扩展，用于构建有状态的、多角色的 Agent 应用，支持循环和分支。", "url": "https://langchain.com/langgraph"},
        ],
    }
    
    # 简单的关键词匹配
    results = []
    for key in mock_results:
        if any(word in query.lower() for word in key.lower().split()):
            results = mock_results[key]
            break
    
    if not results:
        # 默认返回通用结果
        results = [
            {"title": f"关于「{query}」的搜索结果", "content": f"这是关于「{query}」的模拟搜索结果。实际使用时请配置 Tavily API Key 以获取真实搜索结果。", "url": "https://example.com/search"},
        ]
    
    return {
        "success": True,
        "query": query,
        "results": results[:num_results],
    }


# ========== 工具 3：获取当前时间 ==========
@tool
def get_current_time(timezone: str = "Asia/Shanghai") -> Dict[str, Any]:
    """
    获取当前日期和时间。当用户问现在几点、今天几号、星期几时使用。
    
    参数:
        timezone: 时区，默认 Asia/Shanghai（北京时间）
    """
    # 简化版，直接用本地时间
    now = datetime.datetime.now()
    
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    
    return {
        "success": True,
        "timezone": timezone,
        "date": now.strftime("%Y年%m月%d日"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": weekday_names[now.weekday()],
        "timestamp": now.isoformat(),
    }


# ========== 工具 4：Python 代码执行（模拟） ==========
@tool
def code_executor(code: str) -> Dict[str, Any]:
    """
    Python 代码执行器。当你需要运行 Python 代码来验证逻辑、计算结果时使用。
    注意：这是一个安全受限的沙箱环境。
    
    参数:
        code: 要执行的 Python 代码
    """
    import io
    import contextlib
    
    output = io.StringIO()
    
    try:
        # 安全的执行环境
        safe_globals = {
            '__builtins__': {
                'print': print, 'range': range, 'len': len,
                'int': int, 'float': float, 'str': str, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'map': map, 'filter': filter, 'zip': zip,
                'abs': abs, 'round': round, 'min': min, 'max': max,
                'sum': sum, 'sorted': sorted, 'reversed': reversed,
                'enumerate': enumerate, 'type': type,
            },
            'math': __import__('math'),
        }
        
        with contextlib.redirect_stdout(output):
            exec(code, safe_globals, {})
        
        result = output.getvalue()
        
        return {
            "success": True,
            "code": code,
            "output": result or "(无输出)",
        }
    except Exception as e:
        return {
            "success": False,
            "code": code,
            "error": str(e),
        }


# ========== 工具 5：翻译 ==========
@tool
def translate(text: str, target_lang: str = "中文") -> Dict[str, Any]:
    """
    文本翻译工具。当用户需要翻译文本时使用。
    
    参数:
        text: 要翻译的文本
        target_lang: 目标语言，如 "中文"、"英文"、"日文"
    """
    # 模拟翻译（实际项目中调用翻译 API 或 LLM）
    translations = {
        "hello": "你好",
        "world": "世界",
        "good morning": "早上好",
        "thank you": "谢谢",
    }
    
    # 简单的模拟翻译
    if target_lang in ["中文", "Chinese", "zh"]:
        result = translations.get(text.lower(), f"[翻译结果] {text}")
    elif target_lang in ["英文", "English", "en"]:
        reverse = {v: k for k, v in translations.items()}
        result = reverse.get(text, f"[Translation] {text}")
    else:
        result = f"[{target_lang}翻译] {text}"
    
    return {
        "success": True,
        "original_text": text,
        "translated_text": result,
        "target_language": target_lang,
    }


# ========== 工具注册表 ==========
ALL_TOOLS = [
    calculator,
    web_search,
    get_current_time,
    code_executor,
    translate,
]


def get_tool_descriptions() -> List[Dict]:
    """获取所有工具的描述（用于注入 Prompt）"""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "args": tool.args_schema.model_json_schema() if tool.args_schema else {},
        }
        for tool in ALL_TOOLS
    ]
