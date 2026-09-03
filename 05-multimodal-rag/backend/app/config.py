from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8003

    # 模型配置
    CLIP_MODEL_NAME: str = "OFA-Sys/chinese-clip-vit-base-patch16"
    TEXT_EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"
    DEVICE: str = "auto"

    # 向量数据库
    QDRANT_PATH: str = "./data/qdrant"
    QDRANT_COLLECTION: str = "multimodal_content"
    QDRANT_VECTOR_SIZE: int = 512

    # 检索配置
    RETRIEVE_TOP_K: int = 8
    TEXT_WEIGHT: float = 0.5
    IMAGE_WEIGHT: float = 0.5

    # 数据目录
    UPLOAD_DIR: str = "./data/uploads"
    IMAGE_DIR: str = "./data/images"

    class Config:
        env_file = ".env"


settings = Settings()
