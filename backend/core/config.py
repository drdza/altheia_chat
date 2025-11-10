# app/core/config.py

import os
from pydantic import BaseModel, Field, AnyHttpUrl
from dotenv import load_dotenv

load_dotenv()  # carga el .env en os.environ

class Settings(BaseModel):
    # Seguridad
    API_KEY: str = Field(default=os.getenv("API_KEY", "dev-user-key"))
    API_ADMIN_KEY: str = Field(default=os.getenv("API_ADMIN_KEY", "dev-admin-key"))
    ALTHEIA_SQL: str = Field(default=os.getenv("ALTHEIA_SQL", ))

    # LLM Inference (agnóstico por API)
    LLM_API_URL: AnyHttpUrl | str = os.getenv("LLM_API_URL", "http://localhost:8001/chat")
    LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
    LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "30"))

    # Embeddings (elige API externa o local)
    EMBEDDINGS_API_URL: str | None = os.getenv("EMBEDDINGS_API_URL")
    EMBEDDINGS_API_KEY: str | None = os.getenv("EMBEDDINGS_API_KEY")
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "nvidia/nv-embedqa-e5-v5")
    EMBEDDINGS_DIM: int = int(os.getenv("EMBEDDINGS_DIM", "1024"))

    # Milvus
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "127.0.0.1")    
    MILVUS_PORT: str = os.getenv("MILVUS_PORT", "19530")
    MILVUS_COLLECTION: str = os.getenv("MILVUS_COLLECTION", "altheia_docs")
    MILVUS_INDEX_TYPE: str = os.getenv("MILVUS_INDEX_TYPE", "IVF_FLAT")
    MILVUS_METRIC: str = os.getenv("MILVUS_METRIC", "IP")
    MILVUS_TOP_K: int = int(os.getenv("MILVUS_TOP_K", "5"))

    # Active Directory
    AD_SERVER: str = os.getenv("AD_SERVER")
    AD_DOMAIN: str = os.getenv("AD_DOMAIN")
    AD_SEARCH_BASE: str = os.getenv("AD_SEARCH_BASE")

    # JWT
    SECRET_JWT_KEY: str = os.getenv("SECRET_JWT_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480)
    
    # Memoria
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_ADMIN_URL: str = os.getenv("DATABASE_ADMIN_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    
    # Otros
    SERVICE_NAME: str = "altheia-rag"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")





settings = Settings()
