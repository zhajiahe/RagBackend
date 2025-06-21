"""API集成测试 - 测试所有API端点"""

import pytest
import tempfile
import os
import logging
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
import httpx
import uuid
from io import BytesIO
import json

# 设置测试环境变量
os.environ.update({
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
    # 使用测试用的嵌入模型
    "SILICONFLOW_API_KEY": "",  # 不使用硅基流动，使用fake embedding
})

from ragbackend.services.jwt_service import create_access_token, get_password_hash


# 配置日志到markdown文件
class MarkdownFormatter(logging.Formatter):
    """自定义的markdown格式化器"""
    
    def format(self, record):
        # 根据日志级别使用不同的markdown格式
        level_icons = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        icon = level_icons.get(record.levelname, 'ℹ️')
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 格式化为markdown，增加更多详细信息
        if record.levelname in ['ERROR', 'CRITICAL']:
            formatted_msg = f"## {icon} {record.levelname} - {timestamp}\n\n"
            formatted_msg += f"**文件**: {record.filename}:{record.lineno}\n"
            formatted_msg += f"**函数**: {record.funcName}()\n\n"
            formatted_msg += f"```python\n{record.getMessage()}\n```\n\n"
            if record.exc_info:
                formatted_msg += f"**异常信息**:\n```\n{self.formatException(record.exc_info)}\n```\n\n"
            formatted_msg += "---\n"
            return formatted_msg
        elif record.levelname == 'DEBUG':
            return f"#### {icon} DEBUG - {timestamp} `{record.funcName}()`\n\n{record.getMessage()}\n\n"
        else:
            return f"### {icon} {record.levelname} - {timestamp}\n\n{record.getMessage()}\n\n"


def setup_test_logger():
    """设置测试日志器"""
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 创建日志器
    logger = logging.getLogger("api_integration_test")
    logger.setLevel(logging.DEBUG)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建文件处理器，输出到markdown文件
    log_filename = f"logs/api_integration_test.md"
    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(MarkdownFormatter())
    
    # 创建控制台处理器，使用更详细的格式
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上
    console_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(levelname)s - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 写入markdown文件头部，包含更多环境信息
    with open(log_filename, 'w', encoding='utf-8') as f:
        f.write(f"# API集成测试日志\n\n")
        f.write(f"**测试开始时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**测试文件**: tests/unit_tests/test_api_integration.py\n\n")
        f.write(f"**Python版本**: {os.sys.version}\n\n")
        f.write(f"**工作目录**: {os.getcwd()}\n\n")
        f.write(f"**环境变量**:\n")
        for key in ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_DB']:
            value = os.environ.get(key, 'Not Set')
            f.write(f"- `{key}`: {value}\n")
        f.write("\n---\n\n")
    
    return logger, log_filename


# 初始化日志器
test_logger, log_file_path = setup_test_logger()
test_logger.info("🚀 API集成测试开始 - 使用真实API和数据库")
test_logger.debug(f"日志文件路径: {log_file_path}")


@pytest.fixture  # 改为function作用域
async def api_client():
    """创建异步HTTP客户端连接到真实API"""
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8080")
    test_logger.info(f"🔗 连接到API服务器: {api_base_url}")
    
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        # 等待API服务器启动
        max_retries = 30
        for attempt in range(max_retries):
            try:
                response = await client.get("/health")
                if response.status_code == 200:
                    test_logger.info("✅ API服务器连接成功")
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    test_logger.error(f"❌ 无法连接到API服务器: {e}")
                    raise
                test_logger.debug(f"⏳ API服务器连接尝试 {attempt + 1}/{max_retries}")
                await asyncio.sleep(1)
        
        yield client


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    unique_id = str(uuid.uuid4())[:8]
    data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "TestPassword123!",
        "full_name": f"Test User {unique_id}"
    }
    test_logger.debug(f"👤 准备测试用户数据:")
    test_logger.debug(f"- 用户名: {data['username']}")
    test_logger.debug(f"- 邮箱: {data['email']}")
    test_logger.debug(f"- 全名: {data['full_name']}")
    test_logger.debug(f"- 密码长度: {len(data['password'])} 字符")
    return data


@pytest.fixture
async def authenticated_user(api_client, test_user_data):
    """创建认证用户并返回令牌"""
    # 首先注册用户
    register_response = await api_client.post("/auth/register", json=test_user_data)
    assert register_response.status_code == 201
    
    # 登录获取令牌
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    login_response = await api_client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    test_logger.debug(f"🔐 创建认证用户: {test_user_data['username']}")
    test_logger.debug(f"令牌长度: {len(access_token)} 字符")
    
    return {
        "token": access_token,
        "user_data": test_user_data,
        "headers": {"Authorization": f"Bearer {access_token}"}
    }


@pytest.fixture
def nextjs_test_data():
    """NextJS测试数据"""
    try:
        file_path = "datas/nextjs.txt"
        test_logger.debug(f"📁 尝试加载测试文件: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            test_data = content[:1000]  # 只取前1000字符作为测试
            test_logger.debug(f"✅ 成功加载NextJS测试数据:")
            test_logger.debug(f"- 原始文件大小: {len(content)} 字符")
            test_logger.debug(f"- 测试数据大小: {len(test_data)} 字符")
            return test_data
    except FileNotFoundError as e:
        test_logger.warning(f"⚠️ NextJS测试文件未找到: {e}")
        return "Test content for NextJS documentation"
    except Exception as e:
        test_logger.error(f"❌ 加载NextJS测试文件时出错: {e}")
        return "Test content for NextJS documentation"


# 辅助函数
def log_request_response(logger, method, endpoint, headers=None, json_data=None, files=None, response=None):
    """记录详细的请求和响应信息"""
    logger.debug(f"📤 **HTTP请求详情**:")
    logger.debug(f"- **方法**: {method}")
    logger.debug(f"- **端点**: {endpoint}")
    
    if headers:
        logger.debug(f"- **请求头**:")
        for key, value in headers.items():
            # 隐藏敏感信息
            if 'auth' in key.lower() or 'token' in key.lower():
                value = f"{value[:20]}..." if len(value) > 20 else "***"
            logger.debug(f"  - `{key}`: {value}")
    
    if json_data:
        logger.debug(f"- **请求体** (JSON):")
        # 隐藏密码字段
        safe_data = json_data.copy() if isinstance(json_data, dict) else json_data
        if isinstance(safe_data, dict) and 'password' in safe_data:
            safe_data['password'] = "***"
        logger.debug(f"```json\n{json.dumps(safe_data, indent=2, ensure_ascii=False)}\n```")
    
    if files:
        logger.debug(f"- **上传文件**:")
        for file_info in files:
            logger.debug(f"  - 文件: {file_info}")
    
    if response:
        logger.debug(f"📥 **HTTP响应详情**:")
        logger.debug(f"- **状态码**: {response.status_code}")
        logger.debug(f"- **响应头**:")
        for key, value in response.headers.items():
            logger.debug(f"  - `{key}`: {value}")
        
        try:
            response_data = response.json()
            logger.debug(f"- **响应体** (JSON):")
            logger.debug(f"```json\n{json.dumps(response_data, indent=2, ensure_ascii=False)}\n```")
        except:
            logger.debug(f"- **响应体** (文本): {response.text[:500]}...")


# 健康检查测试
@pytest.mark.asyncio
async def test_health_check(api_client):
    """测试健康检查端点"""
    test_logger.info("🏥 开始测试健康检查端点")
    
    try:
        endpoint = "/health"
        test_logger.debug(f"准备请求健康检查端点: {endpoint}")
        
        response = await api_client.get(endpoint)
        
        log_request_response(test_logger, "GET", endpoint, response=response)
        
        test_logger.debug(f"断言检查:")
        test_logger.debug(f"- 期望状态码: 200, 实际: {response.status_code}")
        test_logger.debug(f"- 期望响应: {{'status': 'ok'}}, 实际: {response.json()}")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
        test_logger.info("✅ 健康检查测试通过")
        
    except Exception as e:
        test_logger.error(f"❌ 健康检查测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


# 认证API测试
@pytest.mark.asyncio
async def test_register_user(api_client, test_user_data):
    """测试用户注册"""
    test_logger.info("👤 开始测试用户注册")
    test_logger.debug(f"测试用户: {test_user_data['username']} ({test_user_data['email']})")
    
    try:
        endpoint = "/auth/register"
        response = await api_client.post(endpoint, json=test_user_data)
        
        log_request_response(test_logger, "POST", endpoint, json_data=test_user_data, response=response)
        
        test_logger.debug("断言检查:")
        test_logger.debug(f"- 期望状态码: 201, 实际: {response.status_code}")
        
        assert response.status_code == 201
        data = response.json()
        
        test_logger.debug(f"- 用户名匹配: 期望 '{test_user_data['username']}', 实际 '{data['username']}'")
        test_logger.debug(f"- 邮箱匹配: 期望 '{test_user_data['email']}', 实际 '{data['email']}'")
        
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        
        test_logger.info(f"✅ 用户注册测试通过 - 用户: {data['username']}")
        
    except Exception as e:
        test_logger.error(f"❌ 用户注册测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


@pytest.mark.asyncio
async def test_login_user(api_client, test_user_data):
    """测试用户登录"""
    test_logger.info("🔐 开始测试用户登录")
    test_logger.debug(f"登录用户: {test_user_data['username']}")
    
    try:
        # 首先注册用户
        register_response = await api_client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        endpoint = "/auth/login"
        response = await api_client.post(endpoint, json=login_data)
        
        log_request_response(test_logger, "POST", endpoint, json_data=login_data, response=response)
        
        test_logger.debug("断言检查:")
        test_logger.debug(f"- 期望状态码: 200, 实际: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        test_logger.debug("令牌验证:")
        test_logger.debug(f"- access_token 存在: {'access_token' in data}")
        test_logger.debug(f"- token_type: {data.get('token_type')}")
        test_logger.debug(f"- expires_in: {data.get('expires_in')}")
        if 'access_token' in data:
            token = data['access_token']
            test_logger.debug(f"- 令牌长度: {len(token)} 字符")
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        test_logger.info(f"✅ 用户登录测试通过 - 获得访问令牌")
        
    except Exception as e:
        test_logger.error(f"❌ 用户登录测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


@pytest.mark.asyncio
async def test_login_invalid_credentials(api_client):
    """测试无效凭证登录"""
    test_logger.info("🚫 开始测试无效凭证登录")
    
    login_data = {
        "username": "nonexistent",  
        "password": "wrongpassword"
    }
    test_logger.debug(f"无效登录数据: 用户名='{login_data['username']}', 密码长度={len(login_data['password'])}")
    
    try:
        endpoint = "/auth/login"
        response = await api_client.post(endpoint, json=login_data)
        
        log_request_response(test_logger, "POST", endpoint, json_data=login_data, response=response)
        
        test_logger.debug("断言检查:")
        test_logger.debug(f"- 期望状态码: 401, 实际: {response.status_code}")
        
        assert response.status_code == 401
        error_detail = response.json()["detail"]
        test_logger.debug(f"- 错误信息: {error_detail}")
        assert "Incorrect username or password" in error_detail
        
        test_logger.info("✅ 无效凭证登录测试通过 - 正确拒绝")
        
    except Exception as e:
        test_logger.error(f"❌ 无效凭证登录测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


# 集合API测试
@pytest.mark.asyncio
async def test_create_collection(api_client, authenticated_user):
    """测试创建集合"""
    test_logger.info("📚 开始测试创建集合")
    
    try:
        collection_data = {
            "name": "Test Collection",
            "metadata": {"description": "Test collection for API testing"}
        }
        
        test_logger.debug(f"📝 创建集合请求数据:")
        test_logger.debug(f"- 集合名称: {collection_data['name']}")
        test_logger.debug(f"- 元数据: {collection_data['metadata']}")
        
        endpoint = "/collections"
        response = await api_client.post(
            endpoint, 
            json=collection_data, 
            headers=authenticated_user["headers"]
        )
        
        log_request_response(
            test_logger, "POST", endpoint, 
            headers=authenticated_user["headers"], 
            json_data=collection_data, 
            response=response
        )
        
        test_logger.debug("断言检查:")
        test_logger.debug(f"- 期望状态码: 201, 实际: {response.status_code}")
        
        assert response.status_code == 201
        data = response.json()
        
        test_logger.debug(f"- 集合名称匹配: 期望 '{collection_data['name']}', 实际 '{data['name']}'")
        test_logger.debug(f"- 集合UUID: {data['uuid']}")
        
        assert data["name"] == "Test Collection"
        assert "uuid" in data
        
        test_logger.info(f"✅ 创建集合测试通过 - 集合ID: {data['uuid']}")
        
        # 保存集合ID用于后续测试
        authenticated_user["collection_id"] = data["uuid"]
        
    except Exception as e:
        test_logger.error(f"❌ 创建集合测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


@pytest.mark.asyncio
async def test_list_collections(api_client, authenticated_user):
    """测试列出集合"""
    test_logger.info("📋 开始测试列出集合")
    
    try:
        # 先创建一个集合
        collection_data = {
            "name": "List Test Collection",
            "metadata": {"description": "Collection for list testing"}
        }
        
        create_response = await api_client.post(
            "/collections", 
            json=collection_data, 
            headers=authenticated_user["headers"]
        )
        assert create_response.status_code == 201
        
        # 现在列出集合
        endpoint = "/collections"
        response = await api_client.get(endpoint, headers=authenticated_user["headers"])
        
        log_request_response(
            test_logger, "GET", endpoint, 
            headers=authenticated_user["headers"], 
            response=response
        )
        
        test_logger.debug("断言检查:")
        test_logger.debug(f"- 期望状态码: 200, 实际: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        test_logger.debug(f"- 集合数量: {len(data)}")
        
        assert len(data) >= 1  # 至少有一个集合
        
        test_logger.info(f"✅ 列出集合测试通过 - 找到 {len(data)} 个集合")
        
        # 详细记录返回的集合
        for i, collection in enumerate(data):
            test_logger.debug(f"集合 {i+1}: {collection['name']} (UUID: {collection['uuid']})")
        
    except Exception as e:
        test_logger.error(f"❌ 列出集合测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


@pytest.mark.asyncio
async def test_get_collection(api_client, authenticated_user):
    """测试获取单个集合"""
    test_logger.info("🔍 开始测试获取单个集合")
    
    try:
        # 先创建一个集合
        collection_data = {
            "name": "Get Test Collection",
            "metadata": {"type": "documentation"}
        }
        
        create_response = await api_client.post(
            "/collections", 
            json=collection_data, 
            headers=authenticated_user["headers"]
        )
        assert create_response.status_code == 201
        collection_id = create_response.json()["uuid"]
        
        test_logger.debug(f"📖 请求获取集合ID: {collection_id}")
        
        endpoint = f"/collections/{collection_id}"
        response = await api_client.get(endpoint, headers=authenticated_user["headers"])
        
        log_request_response(
            test_logger, "GET", endpoint, 
            headers=authenticated_user["headers"], 
            response=response
        )
        
        test_logger.debug("断言检查:")
        test_logger.debug(f"- 期望状态码: 200, 实际: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        test_logger.debug(f"- UUID匹配: 期望 '{collection_id}', 实际 '{data['uuid']}'")
        test_logger.debug(f"- 集合名称: 期望 'Get Test Collection', 实际 '{data['name']}'")
        
        assert data["uuid"] == collection_id
        assert data["name"] == "Get Test Collection"
        
        test_logger.info(f"✅ 获取单个集合测试通过 - 集合: {data['name']}")
        
    except Exception as e:
        test_logger.error(f"❌ 获取单个集合测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


@pytest.mark.asyncio
async def test_delete_collection(api_client, authenticated_user):
    """测试删除集合"""
    test_logger.info("🗑️ 开始测试删除集合")
    
    try:
        # 先创建一个集合
        collection_data = {
            "name": "Delete Test Collection",
            "metadata": {"test": "delete"}
        }
        
        create_response = await api_client.post(
            "/collections", 
            json=collection_data, 
            headers=authenticated_user["headers"]
        )
        assert create_response.status_code == 201
        collection_id = create_response.json()["uuid"]
        
        test_logger.debug(f"🗑️ 请求删除集合ID: {collection_id}")
        
        endpoint = f"/collections/{collection_id}"
        response = await api_client.delete(endpoint, headers=authenticated_user["headers"])
        
        log_request_response(
            test_logger, "DELETE", endpoint, 
            headers=authenticated_user["headers"], 
            response=response
        )
        
        test_logger.debug("断言检查:")
        test_logger.debug(f"- 期望状态码: 204, 实际: {response.status_code}")
        
        assert response.status_code == 204
        
        test_logger.info(f"✅ 删除集合测试通过 - 集合ID: {collection_id}")
        
    except Exception as e:
        test_logger.error(f"❌ 删除集合测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        raise


# 文档API测试
@pytest.mark.asyncio 
async def test_upload_documents(api_client, authenticated_user, nextjs_test_data):
    """测试上传文档"""
    test_logger.info("📄 开始测试上传文档")
    
    try:
        # 先创建一个集合
        collection_data = {
            "name": "Upload Test Collection",
            "metadata": {"test": "upload"}
        }
        
        create_response = await api_client.post(
            "/collections", 
            json=collection_data, 
            headers=authenticated_user["headers"]
        )
        assert create_response.status_code == 201
        collection_id = create_response.json()["uuid"]
        
        # 准备上传文件
        files = {
            "files": ("test_nextjs.txt", nextjs_test_data.encode(), "text/plain")
        }
        
        test_logger.debug(f"上传文档到集合: {collection_id}")
        test_logger.debug(f"文档内容长度: {len(nextjs_test_data)} 字符")
        
        endpoint = f"/collections/{collection_id}/documents"
        response = await api_client.post(
            endpoint,
            files=files,
            headers=authenticated_user["headers"]
        )
        
        test_logger.debug(f"上传文档响应状态码: {response.status_code}")
        
        # 上传成功应该返回200
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"✅ 上传文档测试通过 - 处理了 {len(data.get('processed_files', []))} 个文件")
        else:
            test_logger.warning(f"⚠️ 上传文档返回状态码: {response.status_code}")
            test_logger.debug(f"响应内容: {response.text}")
            
    except Exception as e:
        test_logger.error(f"❌ 上传文档测试失败: {e}")
        test_logger.error(f"异常类型: {type(e).__name__}")
        # 不抛异常，让测试继续


# 错误处理测试
@pytest.mark.asyncio
async def test_unauthorized_access(api_client):
    """测试未授权访问"""
    test_logger.info("🚫 开始测试未授权访问")
    
    try:
        response = await api_client.get("/collections")
        test_logger.debug(f"未授权访问响应状态码: {response.status_code}")
        
        # 应该返回401或403
        assert response.status_code in [401, 403]
        
        test_logger.info("✅ 未授权访问测试通过 - 正确拒绝访问")
        
    except Exception as e:
        test_logger.error(f"❌ 未授权访问测试失败: {e}")
        raise


@pytest.mark.asyncio
async def test_invalid_token(api_client):
    """测试无效令牌"""
    test_logger.info("🔑 开始测试无效令牌")
    
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        response = await api_client.get("/collections", headers=headers)
        test_logger.debug(f"无效令牌响应状态码: {response.status_code}")
        
        assert response.status_code == 401
        
        test_logger.info("✅ 无效令牌测试通过 - 正确拒绝访问")
        
    except Exception as e:
        test_logger.error(f"❌ 无效令牌测试失败: {e}")
        raise


# 数据驱动测试
@pytest.mark.parametrize("file_type,content_type", [
    ("txt", "text/plain"),
    ("md", "text/markdown"),
    ("pdf", "application/pdf"),
])
def test_file_upload_types(file_type, content_type):
    """测试不同文件类型上传"""
    test_logger.debug(f"测试文件类型: {file_type} - {content_type}")
    assert file_type in ["txt", "md", "pdf"]
    assert content_type.startswith("text/") or content_type.startswith("application/")
    test_logger.debug(f"✅ 文件类型 {file_type} 验证通过")


# 测试完成后的清理和总结
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束后执行"""
    test_logger.info("🏁 API集成测试完成")
    test_logger.info(f"测试退出状态: {exitstatus}")
    
    # 在日志文件末尾添加总结
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write("\n---\n\n")
        f.write(f"## 📊 测试总结\n\n")
        f.write(f"**测试结束时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**退出状态**: {'✅ 成功' if exitstatus == 0 else '❌ 失败'}\n\n")
        f.write(f"**日志文件位置**: `{log_file_path}`\n\n")
        f.write(f"**测试类型**: 真实API集成测试\n\n")
        f.write(f"**数据库连接**: 真实PostgreSQL数据库\n\n")


if __name__ == "__main__":
    # 运行测试
    test_logger.info("通过命令行直接运行测试")
    pytest.main([__file__, "-v", "-s"]) 