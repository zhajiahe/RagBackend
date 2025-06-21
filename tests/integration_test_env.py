"""集成测试环境变量配置"""

import os

# 测试环境变量配置
TEST_ENV_VARS = {
    "IS_TESTING": "false",  # 使用真实环境
    "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "localhost"),
    "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
    "POSTGRES_USER": os.getenv("POSTGRES_USER", "postgres"),
    "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "POSTGRES_DB": os.getenv("POSTGRES_DB", "postgres"),
    "SECRET_KEY": "test-secret-key-for-integration-tests",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "MINIO_ENDPOINT": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    "MINIO_ACCESS_KEY": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    "MINIO_SECRET_KEY": os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
    "MINIO_SECURE": "false",
    "MINIO_BUCKET_NAME": "test-ragbackend-documents",
    "API_BASE_URL": os.getenv("API_BASE_URL", "http://localhost:8080"),
    # 使用测试用的嵌入模型
    "SILICONFLOW_API_KEY": "",  # 不使用硅基流动，使用fake embedding
    "OPENAI_API_KEY": "",
    "ALLOW_ORIGINS": '["http://localhost:3000"]',
    "DEFAULT_ADMIN_USERNAME": "admin",
    "DEFAULT_ADMIN_EMAIL": "admin@example.com",
    "DEFAULT_ADMIN_PASSWORD": "admin123",
    "DEFAULT_ADMIN_FULL_NAME": "系统管理员"
}


def setup_test_environment():
    """设置测试环境变量"""
    for key, value in TEST_ENV_VARS.items():
        os.environ[key] = value
        
    print("✅ 测试环境变量已设置")
    print(f"📊 数据库: {os.environ['POSTGRES_USER']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}")
    print(f"🔗 API地址: {os.environ['API_BASE_URL']}")
    print(f"💾 MinIO: {os.environ['MINIO_ACCESS_KEY']}@{os.environ['MINIO_ENDPOINT']}")


if __name__ == "__main__":
    setup_test_environment() 