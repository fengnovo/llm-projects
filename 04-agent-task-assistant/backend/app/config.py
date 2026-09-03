from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 模型配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AGENT_MODEL: str = "gpt-3.5-turbo"

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    # Agent 配置
    MAX_AGENT_STEPS: int = 10
    TAVILY_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
