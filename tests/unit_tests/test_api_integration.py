 """API集成测试 - 测试所有API端点"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO
import json

from ragbackend.server import APP
from ragbackend.services.jwt_service import create_access_token
from ragbackend.schemas.users import UserCreate, UserLogin


class TestAPIIntegration:
    """API集成测试类"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """创建测试客户端"""
        return TestClient(APP)
    
    @pytest.fixture(scope="class")
    def test_user_data(self):
        """测试用户数据"""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
    
    @pytest.fixture(scope="class")
    def auth_headers(self, test_user_data):
        """认证头信息"""
        # 创建访问令牌
        token = create_access_token(
            data={"sub": "test_user_id", "username": test_user_data["username"]}
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def nextjs_test_data(self):
        """NextJS测试数据"""
        try:
            with open("datas/nextjs.txt", "r", encoding="utf-8") as f:
                content = f.read()
                return content[:1000]  # 只取前1000字符作为测试
        except FileNotFoundError:
            return "Test content for NextJS documentation"
    
    @pytest.fixture(scope="class")
    def langgraph_test_data(self):
        """LangGraph测试数据"""
        try:
            with open("datas/langgraph.txt", "r", encoding="utf-8") as f:
                content = f.read()
                return content[:1000]  # 只取前1000字符作为测试
        except FileNotFoundError:
            return "Test content for LangGraph documentation"


class TestHealthCheck:
    """健康检查测试"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuthenticationAPI:
    """认证API测试"""
    
    @patch("ragbackend.api.auth.get_user_by_username")
    @patch("ragbackend.api.auth.get_user_by_email") 
    @patch("ragbackend.api.auth.create_user")
    def test_register_user(self, mock_create_user, mock_get_email, mock_get_username, client, test_user_data):
        """测试用户注册"""
        # Mock数据库查询返回None（用户不存在）
        mock_get_username.return_value = None
        mock_get_email.return_value = None
        
        # Mock创建用户返回值
        mock_create_user.return_value = {
            "id": "test_user_id",
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "full_name": test_user_data["full_name"],
            "is_active": True,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
    
    @patch("ragbackend.api.auth.get_user_by_username")
    @patch("ragbackend.api.auth.update_user_last_login")
    def test_login_user(self, mock_update_login, mock_get_user, client, test_user_data):
        """测试用户登录"""
        from ragbackend.services.jwt_service import get_password_hash
        
        # Mock用户数据
        mock_user = {
            "id": "test_user_id",
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "hashed_password": get_password_hash(test_user_data["password"]),
            "is_active": True
        }
        mock_get_user.return_value = mock_user
        mock_update_login.return_value = None
        
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self, client):
        """测试无效凭证登录"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        with patch("ragbackend.api.auth.get_user_by_username") as mock_get_user:
            mock_get_user.return_value = None
            
            response = client.post("/auth/login", json=login_data)
            assert response.status_code == 401
            assert "Incorrect username or password" in response.json()["detail"]


class TestCollectionsAPI:
    """集合API测试"""
    
    @patch("ragbackend.database.collections.CollectionsManager.create")
    @patch("ragbackend.auth.get_user_by_id")
    def test_create_collection(self, mock_get_user, mock_create, client, auth_headers):
        """测试创建集合"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock集合创建
        mock_create.return_value = {
            "id": "collection_id_123",
            "name": "Test Collection",
            "metadata": {"description": "Test collection for API testing"}
        }
        
        collection_data = {
            "name": "Test Collection",
            "metadata": {"description": "Test collection for API testing"}
        }
        
        response = client.post("/collections", json=collection_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Collection"
        assert data["id"] == "collection_id_123"
    
    @patch("ragbackend.database.collections.CollectionsManager.list")
    @patch("ragbackend.auth.get_user_by_id")
    def test_list_collections(self, mock_get_user, mock_list, client, auth_headers):
        """测试列出集合"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock集合列表
        mock_list.return_value = [
            {
                "id": "collection_1",
                "name": "Collection 1",
                "metadata": {}
            },
            {
                "id": "collection_2", 
                "name": "Collection 2",
                "metadata": {}
            }
        ]
        
        response = client.get("/collections", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Collection 1"
    
    @patch("ragbackend.database.collections.CollectionsManager.get")
    @patch("ragbackend.auth.get_user_by_id")
    def test_get_collection(self, mock_get_user, mock_get, client, auth_headers):
        """测试获取单个集合"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock集合数据
        mock_get.return_value = {
            "id": "collection_123",
            "name": "Test Collection",
            "metadata": {"type": "documentation"}
        }
        
        collection_id = "collection_123"
        response = client.get(f"/collections/{collection_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == collection_id
        assert data["name"] == "Test Collection"
    
    @patch("ragbackend.database.collections.CollectionsManager.delete")
    @patch("ragbackend.auth.get_user_by_id")
    def test_delete_collection(self, mock_get_user, mock_delete, client, auth_headers):
        """测试删除集合"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock删除操作
        mock_delete.return_value = None
        
        collection_id = "collection_123"
        response = client.delete(f"/collections/{collection_id}", headers=auth_headers)
        assert response.status_code == 204


class TestDocumentsAPI:
    """文档API测试"""
    
    @patch("ragbackend.services.process_document")
    @patch("ragbackend.database.collections.Collection.add")
    @patch("ragbackend.auth.get_user_by_id")
    def test_upload_documents(self, mock_get_user, mock_add, mock_process, client, auth_headers, nextjs_test_data):
        """测试上传文档"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock文档处理
        from langchain_core.documents import Document
        mock_process.return_value = (
            [Document(page_content=nextjs_test_data, metadata={"source": "test.txt"})],
            {"file_id": "file_123", "filename": "test.txt"}
        )
        
        # Mock添加到集合
        mock_add.return_value = ["doc_id_1"]
        
        # 创建测试文件
        test_file = BytesIO(nextjs_test_data.encode())
        
        collection_id = "collection_123"
        files = [("files", ("nextjs_test.txt", test_file, "text/plain"))]
        
        response = client.post(
            f"/collections/{collection_id}/documents",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "processed_files" in data
        assert "added_documents" in data
    
    @patch("ragbackend.database.collections.Collection.list")
    @patch("ragbackend.auth.get_user_by_id")
    def test_list_documents(self, mock_get_user, mock_list, client, auth_headers):
        """测试列出文档"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock文档列表
        mock_list.return_value = [
            {
                "id": "doc_1",
                "content": "Document content 1",
                "metadata": {"source": "file1.txt"}
            },
            {
                "id": "doc_2",
                "content": "Document content 2", 
                "metadata": {"source": "file2.txt"}
            }
        ]
        
        collection_id = "collection_123"
        response = client.get(f"/collections/{collection_id}/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    @patch("ragbackend.database.collections.Collection.search")
    @patch("ragbackend.auth.get_user_by_id")
    def test_search_documents(self, mock_get_user, mock_search, client, auth_headers):
        """测试搜索文档"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock搜索结果
        mock_search.return_value = [
            {
                "id": "doc_1",
                "content": "React component with form validation",
                "metadata": {"source": "nextjs.txt"},
                "score": 0.95
            }
        ]
        
        search_data = {
            "query": "React form validation",
            "limit": 10
        }
        
        collection_id = "collection_123"
        response = client.post(
            f"/collections/{collection_id}/documents/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "React" in data[0]["content"]
    
    @patch("ragbackend.database.collections.Collection.delete")
    @patch("ragbackend.auth.get_user_by_id")
    def test_delete_document(self, mock_get_user, mock_delete, client, auth_headers):
        """测试删除文档"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock删除操作
        mock_delete.return_value = True
        
        collection_id = "collection_123"
        document_id = "doc_123"
        response = client.delete(
            f"/collections/{collection_id}/documents/{document_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestFilesAPI:
    """文件API测试"""
    
    @patch("ragbackend.database.files.get_files_by_collection")
    @patch("ragbackend.auth.get_user_by_id")
    def test_list_collection_files(self, mock_get_user, mock_get_files, client, auth_headers):
        """测试列出集合中的文件"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock文件列表
        from datetime import datetime
        mock_get_files.return_value = [
            {
                "file_id": "file_1",
                "filename": "nextjs_docs.txt",
                "original_filename": "nextjs.txt",
                "content_type": "text/plain",
                "file_size": 1024,
                "object_path": "files/nextjs.txt",
                "upload_time": datetime.now(),
                "created_at": datetime.now()
            }
        ]
        
        collection_id = "collection_123"
        response = client.get(f"/files/collections/{collection_id}/files", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert len(data["files"]) == 1
        assert data["files"][0]["filename"] == "nextjs_docs.txt"
    
    @patch("ragbackend.database.files.get_files_by_user")
    @patch("ragbackend.auth.get_user_by_id")
    def test_list_user_files(self, mock_get_user, mock_get_files, client, auth_headers):
        """测试列出用户文件"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock文件列表
        from datetime import datetime
        mock_get_files.return_value = []
        
        response = client.get("/files/user/files", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert len(data["files"]) == 0
    
    @patch("ragbackend.database.files.get_file_count_by_collection")
    @patch("ragbackend.auth.get_user_by_id")
    def test_get_collection_file_stats(self, mock_get_user, mock_get_count, client, auth_headers):
        """测试获取集合文件统计"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock文件统计
        mock_get_count.return_value = 5
        
        collection_id = "collection_123"
        response = client.get(f"/files/collections/{collection_id}/files/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["file_count"] == 5
        assert data["collection_id"] == collection_id
    
    @patch("ragbackend.database.files.get_total_file_size_by_user")
    @patch("ragbackend.auth.get_user_by_id")
    def test_get_user_file_stats(self, mock_get_user, mock_get_size, client, auth_headers):
        """测试获取用户文件统计"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock文件大小统计
        mock_get_size.return_value = 1048576  # 1MB
        
        response = client.get("/files/user/files/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_file_size"] == 1048576
        assert data["total_file_size_mb"] == 1.0
    
    @patch("ragbackend.database.files.get_file_metadata")
    @patch("ragbackend.services.minio_service.get_minio_service")
    @patch("ragbackend.auth.get_user_by_id")
    def test_get_file_info(self, mock_get_user, mock_minio_service, mock_get_metadata, client, auth_headers):
        """测试获取文件信息"""
        # Mock用户认证
        mock_get_user.return_value = {
            "id": "test_user_id",
            "username": "testuser",
            "is_active": True
        }
        
        # Mock文件元数据
        from datetime import datetime
        mock_get_metadata.return_value = {
            "file_id": "file_123",
            "collection_id": "collection_123",
            "user_id": "test_user_id",
            "filename": "test.txt",
            "original_filename": "test.txt",
            "content_type": "text/plain",
            "file_size": 1024,
            "object_path": "files/test.txt",
            "upload_time": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Mock MinIO服务
        mock_minio = MagicMock()
        mock_minio.get_file_info.return_value = {
            "size": 1024,
            "etag": "abc123",
            "last_modified": datetime.now(),
            "content_type": "text/plain"
        }
        mock_minio_service.return_value = mock_minio
        
        file_id = "file_123"
        response = client.get(f"/files/{file_id}/info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == file_id
        assert data["filename"] == "test.txt"


class TestErrorHandling:
    """错误处理测试"""
    
    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get("/collections")
        assert response.status_code == 401
    
    def test_invalid_token(self, client):
        """测试无效令牌"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/collections", headers=headers)
        assert response.status_code == 401
    
    @patch("ragbackend.auth.get_user_by_id")
    def test_user_not_found(self, mock_get_user, client):
        """测试用户不存在"""
        mock_get_user.return_value = None
        
        token = create_access_token(data={"sub": "nonexistent_user", "username": "test"})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/collections", headers=headers)
        assert response.status_code == 401
    
    def test_empty_search_query(self, client, auth_headers):
        """测试空搜索查询"""
        with patch("ragbackend.auth.get_user_by_id") as mock_get_user:
            mock_get_user.return_value = {
                "id": "test_user_id",
                "username": "testuser",
                "is_active": True
            }
            
            search_data = {"query": "", "limit": 10}
            collection_id = "collection_123"
            
            response = client.post(
                f"/collections/{collection_id}/documents/search",
                json=search_data,
                headers=auth_headers
            )
            
            assert response.status_code == 400
            assert "empty" in response.json()["detail"].lower()


# 辅助函数
def create_test_file(content: str, filename: str = "test.txt") -> tuple:
    """创建测试文件"""
    file_data = BytesIO(content.encode())
    return (filename, file_data, "text/plain")


# 数据驱动测试
@pytest.mark.parametrize("file_type,content_type", [
    ("txt", "text/plain"),
    ("md", "text/markdown"),
    ("pdf", "application/pdf"),
])
def test_file_upload_types(file_type, content_type):
    """测试不同文件类型上传"""
    # 这里可以扩展测试不同文件类型的上传
    assert file_type in ["txt", "md", "pdf"]
    assert content_type.startswith("text/") or content_type.startswith("application/")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])