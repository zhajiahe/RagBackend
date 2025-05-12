"""Auth to resolve user object."""

import os
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from gotrue.types import User
from starlette.authentication import BaseUser
from supabase import create_client
from typing import Annotated

IS_TESTING = os.environ.get("IS_TESTING", "false").lower() == "true"

security = HTTPBearer()


class AuthenticatedUser(BaseUser):
    """An authenticated user following the Starlette authentication model."""

    def __init__(self, user_id: str, display_name: str) -> None:
        """Initialize the AuthenticatedUser.

        Args:
            user_id: Unique identifier for the user.
            display_name: Display name for the user.
        """
        self.user_id = user_id
        self._display_name = display_name

    @property
    def is_authenticated(self) -> bool:
        """Return True if the user is authenticated."""
        return True

    @property
    def display_name(self) -> str:
        """Return the display name of the user."""
        return self._display_name

    @property
    def identity(self) -> str:
        """Return the identity of the user. This is a unique identifier."""
        return self.user_id


def get_current_user(authorization: str) -> User:
    """Authenticate a user by validating their JWT token against Supabase.

    This function verifies the provided JWT token by making a request to Supabase.
    It requires the SUPABASE_URL and SUPABASE_KEY environment variables to be
    properly configured.

    Args:
        authorization: JWT token string to validate

    Returns:
        User: A Supabase User object containing the authenticated user's information

    Raises:
        HTTPException: With status code 500 if Supabase configuration is missing
        HTTPException: With status code 401 if token is invalid or authentication fails
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase URL or key not found")

    supabase = create_client(supabase_url, supabase_key)

    try:
        response = supabase.auth.get_user(authorization)
        user = response.user

        if not user:
            raise HTTPException(
                status_code=401, detail="Invalid token or user not found"
            )

        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {e!s}")


def resolve_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> AuthenticatedUser | None:
    """Resolve user from the credentials."""
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if IS_TESTING:
        if credentials.credentials in {"user1", "user2"}:
            return AuthenticatedUser(credentials.credentials, credentials.credentials)

    user = get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthenticatedUser(user.id, user.user_metadata.get("name", "User"))
