"""
情绪与好感度状态机

原理：
- 每次对话后，分析用户输入和AI回复，更新情绪状态
- 情绪是多维的（开心、悲伤、生气、害怕、爱慕、害羞）
- 好感度是独立维度，根据互动积极程度变化
- 情绪会影响 AI 的回复风格（通过 Prompt 注入）
"""
from typing import Dict, Tuple
from pydantic import BaseModel


class EmotionUpdate(BaseModel):
    """情绪变化量"""
    happiness: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    love: float = 0.0
    shyness: float = 0.0
    affection: float = 0.0


class EmotionStateMachine:
    """情绪状态机"""

    # 情绪维度列表
    EMOTION_DIMS = ["happiness", "sadness", "anger", "fear", "love", "shyness", "affection"]

    def __init__(self, initial_state: Dict[str, float]):
        self.state = {dim: initial_state.get(dim, 50.0) for dim in self.EMOTION_DIMS}
        # 确保数值在 0-100 之间
        self._clamp()

    def _clamp(self):
        """限制情绪值在 0-100 范围内"""
        for dim in self.EMOTION_DIMS:
            self.state[dim] = max(0.0, min(100.0, self.state[dim]))

    def update(self, delta: EmotionUpdate):
        """更新情绪状态"""
        for dim in self.EMOTION_DIMS:
            self.state[dim] += getattr(delta, dim)
        self._clamp()

    def get_state(self) -> Dict[str, float]:
        return self.state.copy()

    def get_dominant_emotions(self, top_n: int = 3) -> list:
        """获取当前最强烈的几种情绪"""
        sorted_emotions = sorted(
            [(dim, self.state[dim]) for dim in self.EMOTION_DIMS if dim != "affection"],
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_emotions[:top_n]

    def get_mood_text(self) -> str:
        """获取当前心情的文字描述（用于注入 Prompt）"""
        dominant = self.get_dominant_emotions(top_n=2)
        affection = self.state["affection"]

        parts = []
        for name, value in dominant:
            if value > 60:
                parts.append(f"很{_emotion_name(name)}")
            elif value > 40:
                parts.append(f"有点{_emotion_name(name)}")

        if affection >= 80:
            parts.append("对对方非常有好感")
        elif affection >= 60:
            parts.append("对对方很有好感")
        elif affection >= 40:
            parts.append("对对方有点好感")

        return "，".join(parts) if parts else "心情平静"

    def get_affection_level(self) -> str:
        """获取好感度等级描述"""
        aff = self.state["affection"]
        if aff >= 80:
            return "恋人"
        elif aff >= 60:
            return "暧昧"
        elif aff >= 40:
            return "好友"
        elif aff >= 20:
            return "朋友"
        else:
            return "陌生人"


def _emotion_name(key: str) -> str:
    """情绪维度的中文名"""
    mapping = {
        "happiness": "开心",
        "sadness": "悲伤",
        "anger": "生气",
        "fear": "害怕",
        "love": "爱慕",
        "shyness": "害羞",
    }
    return mapping.get(key, key)


def analyze_emotion_from_text(text: str, role: str = "user") -> EmotionUpdate:
    """
    简单的情绪分析（基于关键词，实际项目可以用模型分析）
    
    这是一个简化版，用关键词匹配来估算情绪变化。
    生产环境可以用 LLM 来分析，效果更好。
    """
    delta = EmotionUpdate()

    # 用户发言对 AI 情绪的影响
    if role == "user":
        # 正面词汇 → 开心↑、爱慕↑
        positive_words = ["喜欢", "爱", "想你", "可爱", "漂亮", "帅", "好棒", "厉害", "感谢", "谢谢", "开心", "哈哈"]
        for w in positive_words:
            if w in text:
                delta.happiness += 3
                delta.love += 2
                delta.affection += 1

        # 赞美 → 害羞↑
        compliment_words = ["你真", "你好", "最美", "最棒", "喜欢你"]
        for w in compliment_words:
            if w in text:
                delta.shyness += 5

        # 负面词汇 → 生气↑、悲伤↑
        negative_words = ["讨厌", "烦", "滚", "笨", "丑", "无聊", "不好"]
        for w in negative_words:
            if w in text:
                delta.anger += 5
                delta.sadness += 3
                delta.happiness -= 3
                delta.affection -= 1

        # 关心 → 好感↑、开心↑
        care_words = ["注意身体", "早点睡", "加油", "辛苦了", "没事吧", "还好吗"]
        for w in care_words:
            if w in text:
                delta.affection += 3
                delta.happiness += 5
                delta.love += 2

    return delta


def generate_emotion_prompt(state: Dict[str, float]) -> str:
    """
    根据当前情绪状态，生成注入到 System Prompt 的情绪提示
    让 AI 的回复符合当前情绪
    """
    mood = EmotionStateMachine(state).get_mood_text()
    affection_level = EmotionStateMachine(state).get_affection_level()

    return f"""
【当前状态】
- 心情：{mood}
- 与对方的关系：{affection_level}（好感度 {int(state['affection'])}/100）

请根据当前的心情和关系来回复，保持情绪的一致性。
如果心情不好，不要假装开心；如果好感度高，可以更亲密一些。
"""
