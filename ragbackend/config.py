import json

from langchain_core.embeddings import Embeddings
from starlette.config import Config, undefined

env = Config()

IS_TESTING = env("IS_TESTING", cast=str, default="").lower() == "true"

# JWT Configuration
SECRET_KEY = env("SECRET_KEY", cast=str, default="your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = env("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=60 * 24 * 7)  # 7 days

# Silicon Flow Configuration
SILICONFLOW_API_KEY = env("SILICONFLOW_API_KEY", cast=str, default="")
SILICONFLOW_BASE_URL = env("SILICONFLOW_BASE_URL", cast=str, default="https://api.siliconflow.cn/v1")
SILICONFLOW_MODEL = env("SILICONFLOW_MODEL", cast=str, default="BAAI/bge-m3")


def get_embeddings() -> Embeddings:
    """Get the embeddings instance based on the environment."""
    if IS_TESTING:
        from langchain_core.embeddings import DeterministicFakeEmbedding
        return DeterministicFakeEmbedding(size=512)
    
    # 优先使用硅基流动的嵌入API
    if SILICONFLOW_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                api_key=SILICONFLOW_API_KEY,
                base_url=SILICONFLOW_BASE_URL,
                model=SILICONFLOW_MODEL,
            )
        except ImportError:
            print("Warning: langchain_openai not available, falling back to OpenAI")
    
    # 回退到OpenAI
    try:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings()
    except ImportError:
        # Fallback to fake embedding if OpenAI is not available
        from langchain_core.embeddings import DeterministicFakeEmbedding
        return DeterministicFakeEmbedding(size=512)


# Initialize embeddings lazily to avoid import errors
DEFAULT_EMBEDDINGS = None


def get_default_embeddings() -> Embeddings:
    """Get the default embeddings instance, initializing if needed."""
    global DEFAULT_EMBEDDINGS
    if DEFAULT_EMBEDDINGS is None:
        DEFAULT_EMBEDDINGS = get_embeddings()
    return DEFAULT_EMBEDDINGS
DEFAULT_COLLECTION_NAME = "default_collection"


# Database configuration
POSTGRES_HOST = env("POSTGRES_HOST", cast=str, default="localhost")
POSTGRES_PORT = env("POSTGRES_PORT", cast=int, default="5432")
POSTGRES_USER = env("POSTGRES_USER", cast=str, default="langchain")
POSTGRES_PASSWORD = env("POSTGRES_PASSWORD", cast=str, default="langchain")
POSTGRES_DB = env("POSTGRES_DB", cast=str, default="langchain_test")

# MinIO Configuration
MINIO_ENDPOINT = env("MINIO_ENDPOINT", cast=str, default="localhost:9000")
MINIO_ACCESS_KEY = env("MINIO_ACCESS_KEY", cast=str, default="minioadmin")
MINIO_SECRET_KEY = env("MINIO_SECRET_KEY", cast=str, default="minioadmin123")
MINIO_SECURE = env("MINIO_SECURE", cast=bool, default=False)
MINIO_BUCKET_NAME = env("MINIO_BUCKET_NAME", cast=str, default="ragbackend-documents")

# Read allowed origins from environment variable
ALLOW_ORIGINS_JSON = env("ALLOW_ORIGINS", cast=str, default="")

if ALLOW_ORIGINS_JSON:
    ALLOWED_ORIGINS = json.loads(ALLOW_ORIGINS_JSON.strip())
    print(f"ALLOW_ORIGINS environment variable set to: {ALLOW_ORIGINS_JSON}")
else:
    ALLOWED_ORIGINS = "http://localhost:3000"
    print("ALLOW_ORIGINS environment variable not set.")
