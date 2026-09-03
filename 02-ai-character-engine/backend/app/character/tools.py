"""
Function Calling 工具系统

示例工具：
1. unlock_gallery - 解锁隐藏图集（模拟打赏/付费功能）
2. get_weather - 查询天气（演示工具调用的基本模式）

扩展思路：
- 计费相关：查询余额、购买道具
- 内容相关：推荐歌曲、发送图片
- 系统相关：切换角色、清空记忆
"""
from typing import List, Dict, Any, Callable
from pydantic import BaseModel, Field


# ========== 工具定义 ==========

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "unlock_gallery",
            "description": "解锁隐藏图集。当用户表达了想要看隐藏照片、图集、或者好感度足够高用户主动要求解锁时调用。需要消耗好感度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "gallery_id": {
                        "type": "string",
                        "description": "图集ID，可选值：'daily'（日常照）、'cosplay'（COS照）、'vacation'（度假照）",
                        "enum": ["daily", "cosplay", "vacation"]
                    },
                    "reason": {
                        "type": "string",
                        "description": "用户想要解锁的原因，简单描述"
                    }
                },
                "required": ["gallery_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气。当用户问天气相关的问题时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，比如：北京、上海、深圳"
                    }
                },
                "required": ["city"]
            }
        }
    },
]


# ========== 工具实现 ==========

async def unlock_gallery(gallery_id: str, reason: str = "") -> Dict[str, Any]:
    """解锁隐藏图集（模拟实现）"""
    gallery_info = {
        "daily": {"name": "日常照", "count": 12, "cost_affection": 30},
        "cosplay": {"name": "COS照", "count": 8, "cost_affection": 50},
        "vacation": {"name": "度假照", "count": 15, "cost_affection": 80},
    }

    info = gallery_info.get(gallery_id)
    if not info:
        return {"success": False, "message": "图集不存在"}

    # 实际项目中这里应该检查用户余额/好感度，然后发放权益
    # 这里只是模拟
    return {
        "success": True,
        "message": f"已解锁{info['name']}，共 {info['count']} 张照片",
        "gallery_id": gallery_id,
        "gallery_name": info["name"],
        "photo_count": info["count"],
        "preview_images": [
            f"https://example.com/gallery/{gallery_id}/1.jpg",
            f"https://example.com/gallery/{gallery_id}/2.jpg",
            f"https://example.com/gallery/{gallery_id}/3.jpg",
        ]
    }


async def get_weather(city: str) -> Dict[str, Any]:
    """查询天气（模拟实现）"""
    # 实际项目中调用真实的天气 API
    mock_weather = {
        "北京": {"temp": 25, "weather": "晴", "wind": "东北风 3级", "humidity": "45%"},
        "上海": {"temp": 28, "weather": "多云", "wind": "东南风 2级", "humidity": "65%"},
        "深圳": {"temp": 32, "weather": "雷阵雨", "wind": "南风 3级", "humidity": "80%"},
    }

    data = mock_weather.get(city, {"temp": 26, "weather": "晴转多云", "wind": "微风", "humidity": "50%"})
    return {
        "success": True,
        "city": city,
        **data,
        "suggestion": "记得根据天气做好准备哦~"
    }


# 工具函数字典
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "unlock_gallery": unlock_gallery,
    "get_weather": get_weather,
}


async def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行工具调用"""
    if name not in TOOL_FUNCTIONS:
        return {"success": False, "error": f"工具 {name} 不存在"}

    try:
        result = await TOOL_FUNCTIONS[name](**arguments)
        return result
    except Exception as e:
        return {"success": False, "error": f"工具执行失败: {str(e)}"}
