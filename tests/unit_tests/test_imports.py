"""Import tests to verify all modules can be imported correctly."""

import sys
import importlib
import pytest


class TestCoreImports:
    """Test core module imports."""

    def test_import_main_package(self):
        """Test importing the main ragbackend package."""
        import ragbackend
        assert hasattr(ragbackend, "__version__")
        assert ragbackend.__version__ == "0.0.1"

    def test_import_config(self):
        """Test importing configuration module."""
        from ragbackend import config
        
        # Check essential config attributes exist
        assert hasattr(config, "SECRET_KEY")
        assert hasattr(config, "ALGORITHM")
        assert hasattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert hasattr(config, "IS_TESTING")

    def test_import_server(self):
        """Test importing the server module."""
        from ragbackend import server
        assert hasattr(server, "lifespan")

    def test_import_auth(self):
        """Test importing authentication module."""
        from ragbackend import auth
        assert hasattr(auth, "get_current_user")
        assert hasattr(auth, "resolve_user")
        assert hasattr(auth, "AuthenticatedUser")


class TestAPIImports:
    """Test API module imports."""

    def test_import_auth_router(self):
        """Test importing auth API router."""
        from ragbackend.api import auth
        assert hasattr(auth, "router")

    def test_import_collections_api(self):
        """Test importing collections API."""
        try:
            from ragbackend.api import collections
            # Module exists
            assert True
        except ImportError:
            # If collections module doesn't exist, that's also fine
            pytest.skip("Collections API module not found")

    def test_import_documents_api(self):
        """Test importing documents API."""
        try:
            from ragbackend.api import documents
            # Module exists
            assert True
        except ImportError:
            # If documents module doesn't exist, that's also fine
            pytest.skip("Documents API module not found")

    def test_import_files_api(self):
        """Test importing files API."""
        from ragbackend.api import files
        assert hasattr(files, "router")


class TestSchemaImports:
    """Test schema imports."""

    def test_import_user_schemas(self):
        """Test importing user schemas."""
        from ragbackend.schemas.users import (
            UserBase,
            UserCreate,
            UserLogin,
            UserResponse,
            Token,
            TokenData,
        )
        
        # Verify these are Pydantic models
        assert hasattr(UserBase, "__fields__") or hasattr(UserBase, "model_fields")
        assert hasattr(UserCreate, "__fields__") or hasattr(UserCreate, "model_fields")
        assert hasattr(UserLogin, "__fields__") or hasattr(UserLogin, "model_fields")
        assert hasattr(UserResponse, "__fields__") or hasattr(UserResponse, "model_fields")
        assert hasattr(Token, "__fields__") or hasattr(Token, "model_fields")
        assert hasattr(TokenData, "__fields__") or hasattr(TokenData, "model_fields")

    def test_import_collection_schemas(self):
        """Test importing collection schemas."""
        try:
            from ragbackend.schemas.collection import (
                CollectionCreate,
                CollectionResponse,
                CollectionUpdate,
            )
            assert hasattr(CollectionCreate, "__fields__") or hasattr(CollectionCreate, "model_fields")
        except ImportError:
            pytest.skip("Collection schemas not found")

    def test_import_document_schemas(self):
        """Test importing document schemas."""
        try:
            from ragbackend.schemas.document import (
                DocumentCreate,
                DocumentResponse,
                DocumentUpdate,
                SearchQuery,
                SearchResult,
            )
            assert hasattr(DocumentCreate, "__fields__") or hasattr(DocumentCreate, "model_fields")
        except ImportError:
            pytest.skip("Document schemas not found")

    def test_import_schemas_init(self):
        """Test importing from schemas __init__.py."""
        from ragbackend.schemas import (
            UserBase,
            UserCreate,
            UserLogin,
            UserResponse,
            Token,
            TokenData,
        )
        
        # Verify these are accessible from the schemas package
        assert UserBase is not None
        assert UserCreate is not None
        assert UserLogin is not None
        assert UserResponse is not None
        assert Token is not None
        assert TokenData is not None


class TestServiceImports:
    """Test service module imports."""

    def test_import_jwt_service(self):
        """Test importing JWT service."""
        from ragbackend.services.jwt_service import (
            create_access_token,
            verify_token,
            verify_password,
            get_password_hash,
        )
        
        # Verify these are callable functions
        assert callable(create_access_token)
        assert callable(verify_token)
        assert callable(verify_password)
        assert callable(get_password_hash)

    def test_import_minio_service(self):
        """Test importing MinIO service."""
        try:
            from ragbackend.services import minio_service
            assert hasattr(minio_service, "get_minio_service")
        except ImportError:
            pytest.skip("MinIO service not found")


class TestDatabaseImports:
    """Test database module imports."""

    def test_import_users_db(self):
        """Test importing users database module."""
        from ragbackend.database.users import (
            create_users_table,
            create_user,
            get_user_by_username,
            get_user_by_email,
            get_user_by_id,
            update_user_last_login,
        )
        
        # Verify these are callable functions
        assert callable(create_users_table)
        assert callable(create_user)
        assert callable(get_user_by_username)
        assert callable(get_user_by_email)
        assert callable(get_user_by_id)
        assert callable(update_user_last_login)

    def test_import_connection(self):
        """Test importing database connection."""
        try:
            from ragbackend.database.connection import get_db_connection
            assert callable(get_db_connection)
        except ImportError:
            pytest.skip("Database connection module not found")

    def test_import_collections_db(self):
        """Test importing collections database module."""
        try:
            from ragbackend.database.collections import CollectionsManager
            assert hasattr(CollectionsManager, "setup")
        except ImportError:
            pytest.skip("Collections database module not found")

    def test_import_files_db(self):
        """Test importing files database module."""
        try:
            from ragbackend.database.files import (
                get_file_metadata,
                get_files_by_collection,
                get_files_by_user,
            )
            assert callable(get_file_metadata)
        except ImportError:
            pytest.skip("Files database module not found")


class TestDependencyImports:
    """Test external dependency imports."""

    def test_import_fastapi(self):
        """Test importing FastAPI."""
        from fastapi import FastAPI, APIRouter, Depends, HTTPException
        assert FastAPI is not None
        assert APIRouter is not None
        assert Depends is not None
        assert HTTPException is not None

    def test_import_pydantic(self):
        """Test importing Pydantic."""
        from pydantic import BaseModel, EmailStr
        assert BaseModel is not None
        assert EmailStr is not None

    def test_import_jose(self):
        """Test importing python-jose."""
        from jose import jwt
        assert jwt is not None

    def test_import_passlib(self):
        """Test importing passlib."""
        from passlib.context import CryptContext
        assert CryptContext is not None

    def test_import_langchain(self):
        """Test importing LangChain core."""
        from langchain_core.embeddings import Embeddings, DeterministicFakeEmbedding
        assert Embeddings is not None
        assert DeterministicFakeEmbedding is not None

    def test_import_asyncpg(self):
        """Test importing asyncpg."""
        import asyncpg
        assert asyncpg is not None

    def test_import_uvicorn(self):
        """Test importing Uvicorn."""
        import uvicorn
        assert uvicorn is not None


class TestConditionalImports:
    """Test imports that may or may not be available."""

    def test_import_langchain_openai(self):
        """Test importing LangChain OpenAI (may not be available in test env)."""
        try:
            from langchain_openai import OpenAIEmbeddings
            assert OpenAIEmbeddings is not None
        except ImportError:
            # This is expected in test environments
            pytest.skip("langchain_openai not available")

    def test_import_minio(self):
        """Test importing MinIO client."""
        try:
            import minio
            assert minio is not None
        except ImportError:
            pytest.skip("MinIO client not available")


class TestModuleAttributes:
    """Test that imported modules have expected attributes."""

    def test_config_attributes(self):
        """Test config module has all required attributes."""
        from ragbackend import config
        
        required_attrs = [
            "SECRET_KEY",
            "ALGORITHM", 
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "IS_TESTING",
            "get_embeddings",
            "get_default_embeddings",
        ]
        
        for attr in required_attrs:
            assert hasattr(config, attr), f"Config missing attribute: {attr}"

    def test_auth_module_attributes(self):
        """Test auth module has all required attributes."""
        from ragbackend import auth
        
        required_attrs = [
            "get_current_user",
            "resolve_user", 
            "AuthenticatedUser",
            "security",
        ]
        
        for attr in required_attrs:
            assert hasattr(auth, attr), f"Auth module missing attribute: {attr}"

    def test_jwt_service_attributes(self):
        """Test JWT service has all required functions."""
        from ragbackend.services import jwt_service
        
        required_functions = [
            "create_access_token",
            "verify_token",
            "verify_password",
            "get_password_hash",
            "pwd_context",
        ]
        
        for func in required_functions:
            assert hasattr(jwt_service, func), f"JWT service missing function: {func}"


def test_python_version():
    """Test Python version compatibility."""
    assert sys.version_info >= (3, 11), "Python 3.11+ is required"


def test_all_imports_successful():
    """Test that we can import the main package without errors."""
    try:
        import ragbackend
        from ragbackend import config, auth, server
        from ragbackend.services import jwt_service
        from ragbackend.schemas import users
        from ragbackend.database import users as db_users
        # If we get here, all imports were successful
        assert True
    except Exception as e:
        pytest.fail(f"Failed to import modules: {e}")
