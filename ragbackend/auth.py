"""Auth to resolve user object."""

from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.authentication import BaseUser

from ragbackend import config
from ragbackend.services.jwt_service import verify_token
from ragbackend.database.users import get_user_by_id

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


async def get_current_user(authorization: str) -> dict:
    """Authenticate a user by validating their JWT token.

    This function verifies the provided JWT token and retrieves the user
    from the database.

    Args:
        authorization: JWT token string to validate

    Returns:
        dict: A user dictionary containing the authenticated user's information

    Raises:
        HTTPException: With status code 401 if token is invalid or authentication fails
    """
    payload = verify_token(authorization)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_active"):
        raise HTTPException(status_code=401, detail="User account is inactive")
    
    return user


async def resolve_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> AuthenticatedUser | None:
    """Resolve user from the credentials."""
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if config.IS_TESTING:
        if credentials.credentials in {"user1", "user2"}:
            return AuthenticatedUser(credentials.credentials, credentials.credentials)
        raise HTTPException(
            status_code=401, detail="Invalid credentials or user not found"
        )

    user = await get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthenticatedUser(user["id"], user.get("full_name") or user["username"])
