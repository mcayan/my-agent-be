from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    APP_NAME: str = "My Agent API"
    DEBUG: bool = True
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "agent-images"
    MINIO_SECURE: bool = False
    
    # API Keys
    SERPER_API_KEY: str = ""  # 可选 - 图片搜索功能需要
    GOOGLE_API_KEY: str = ""  # 可选 - 如果不用 Google Gemini
    OPENAI_API_KEY: str = ""  # 可选 - OpenAI API Key
    DOUBAO_API_KEY: str = ""  # 可选 - 豆包图片生成 API
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

