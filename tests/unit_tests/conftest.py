import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio

os.environ["OPENAI_API_KEY"] = "test_key"
os.environ["IS_TESTING"] = "true"


@pytest_asyncio.fixture(scope="function")
async def async_client():
    """Create an async test client."""
    from ragbackend.server import APP
    from httpx import AsyncClient
    
    async with AsyncClient(app=APP, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_all_db_operations():
    """Mock all database operations comprehensively."""
    patches = [
        patch("ragbackend.database.connection.get_db_connection"),
        patch("ragbackend.database.connection.get_vectorstore"),
        patch("ragbackend.services.minio_service.get_minio_service"),
    ]
    
    mocks = {}
    for p in patches:
        mock = p.start()
        # Configure async mocks
        if hasattr(mock, 'return_value'):
            if 'get_db_connection' in str(p):
                mock_conn = AsyncMock()
                mock.__aenter__ = AsyncMock(return_value=mock_conn)
                mock.__aexit__ = AsyncMock(return_value=None)
                mock.return_value = mock
            else:
                mock.return_value = AsyncMock()
        mocks[str(p)] = mock
    
    yield mocks
    
    for p in patches:
        p.stop()


@pytest.fixture(autouse=True)
def mock_auth_in_testing():
    """Ensure auth works properly in testing mode."""
    with patch("ragbackend.config.IS_TESTING", True):
        yield
