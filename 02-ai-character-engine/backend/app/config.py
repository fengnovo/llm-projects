from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 模型配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    CHAT_MODEL: str = "gpt-3.5-turbo"
    SUMMARY_MODEL: str = "gpt-3.5-turbo"

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/character.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # 角色引擎配置
    SHORT_TERM_MEMORY_WINDOW: int = 20
    LONG_TERM_SUMMARY_INTERVAL: int = 10
    MAX_TOTAL_TOKENS: int = 4000

    class Config:
        env_file = ".env"


settings = Settings()
