from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 模型配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    CHAT_MODEL: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # 向量库
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"

    # RAG 配置
    RETRIEVE_TOP_K: int = 4
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
