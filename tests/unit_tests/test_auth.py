"""Authentication tests."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from ragbackend.services.jwt_service import (
    create_access_token,
    verify_token,
    verify_password,
    get_password_hash,
)
from ragbackend.auth import get_current_user, resolve_user, AuthenticatedUser
from ragbackend import config


class TestJWTService:
    """Test JWT service functions."""

    def test_verify_password_valid(self):
        """Test password verification with valid password."""
        password = "test_password"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_invalid(self):
        """Test password verification with invalid password."""
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "test_password"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are typically 60 characters

    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 20
        
        # Verify token can be decoded
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "user123", "username": "testuser"}
        expires_delta = timedelta(minutes=30)
        
        # Record time before creating token
        current_time = datetime.utcnow()
        token = create_access_token(data, expires_delta)
        
        payload = verify_token(token)
        assert payload is not None
        
        # Check expiry is approximately 30 minutes from now
        # Use utcfromtimestamp since JWT tokens use UTC timestamps
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = current_time + expires_delta
        
        # Allow some tolerance (within 1 minute)
        time_diff = abs((exp_time - expected_time).total_seconds())
        assert time_diff < 60, f"Token expiry time difference is {time_diff} seconds, expected < 60"

    def test_verify_token_valid(self):
        """Test verifying valid token."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"

    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_token_expired(self):
        """Test verifying expired token."""
        data = {"sub": "user123", "username": "testuser"}
        # Create token that expires immediately
        expired_token = create_access_token(data, timedelta(seconds=-1))
        
        payload = verify_token(expired_token)
        assert payload is None


class TestAuthenticatedUser:
    """Test AuthenticatedUser class."""

    def test_authenticated_user_creation(self):
        """Test creating an authenticated user."""
        user = AuthenticatedUser("user123", "Test User")
        
        assert user.user_id == "user123"
        assert user.display_name == "Test User"
        assert user.identity == "user123"
        assert user.is_authenticated is True

    def test_authenticated_user_properties(self):
        """Test authenticated user properties."""
        user = AuthenticatedUser("test_id", "Test Display")
        
        assert user.user_id == "test_id"
        assert user.display_name == "Test Display"
        assert user.identity == "test_id"
        assert user.is_authenticated is True


class TestAuthFunctions:
    """Test authentication functions."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test getting current user with valid token."""
        # Mock the database function
        mock_user = {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True
        }
        
        with patch("ragbackend.auth.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = mock_user
            
            # Create a valid token
            data = {"sub": "user123", "username": "testuser"}
            token = create_access_token(data)
            
            user = await get_current_user(token)
            
            assert user == mock_user
            mock_get_user.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self):
        """Test getting current user with token missing sub claim."""
        # Create token without 'sub' claim
        data = {"username": "testuser"}
        token = create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token payload"

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test getting current user when user not found in database."""
        with patch("ragbackend.auth.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None
            
            data = {"sub": "nonexistent_user", "username": "testuser"}
            token = create_access_token(data)
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "User not found"

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self):
        """Test getting current user when user is inactive."""
        mock_user = {
            "id": "user123",
            "username": "testuser", 
            "email": "test@example.com",
            "is_active": False
        }
        
        with patch("ragbackend.auth.get_user_by_id", new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = mock_user
            
            data = {"sub": "user123", "username": "testuser"}
            token = create_access_token(data)
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "User account is inactive"

    @pytest.mark.asyncio
    async def test_resolve_user_testing_mode(self):
        """Test resolving user in testing mode."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Mock testing mode
        with patch.object(config, 'IS_TESTING', True):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", 
                credentials="user1"
            )
            
            user = await resolve_user(credentials)
            
            assert isinstance(user, AuthenticatedUser)
            assert user.user_id == "user1"
            assert user.display_name == "user1"

    @pytest.mark.asyncio
    async def test_resolve_user_testing_mode_invalid(self):
        """Test resolving user in testing mode with invalid credentials."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        with patch.object(config, 'IS_TESTING', True):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", 
                credentials="invalid_user"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await resolve_user(credentials)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid credentials or user not found"

    @pytest.mark.asyncio
    async def test_resolve_user_invalid_scheme(self):
        """Test resolving user with invalid authentication scheme."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Basic", 
            credentials="token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await resolve_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authentication scheme"

    @pytest.mark.asyncio
    async def test_resolve_user_empty_credentials(self):
        """Test resolving user with empty credentials."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", 
            credentials=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await resolve_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_resolve_user_production_mode(self):
        """Test resolving user in production mode."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_user = {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True
        }
        
        with patch.object(config, 'IS_TESTING', False), \
             patch("ragbackend.auth.get_current_user", new_callable=AsyncMock) as mock_get_current_user:
            
            mock_get_current_user.return_value = mock_user
            
            data = {"sub": "user123", "username": "testuser"}
            token = create_access_token(data)
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", 
                credentials=token
            )
            
            user = await resolve_user(credentials)
            
            assert isinstance(user, AuthenticatedUser)
            assert user.user_id == "user123"
            assert user.display_name == "Test User"
            mock_get_current_user.assert_called_once_with(token) 