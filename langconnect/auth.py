"""Auth to resolve user object."""

import os
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.authentication import BaseUser

app = FastAPI()

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


def resolve_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> AuthenticatedUser:
    """Resolve user from the credentials."""
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if "IS_TESTING" not in os.environ:
        raise AssertionError(
            "Environment variable 'IS_TESTING' not set. "
            "This function should only be called in a testing environment until "
            "the JWT verification logic is implemented."
        )

    # For testing purposes. Replace with JWT verification logic.
    if credentials.credentials == "user1":
        return AuthenticatedUser("user1", "User One")

    if credentials.credentials == "user2":
        return AuthenticatedUser("user2", "User Two")

    # If the credentials are not recognized, raise an error
    raise HTTPException(status_code=401, detail="Invalid credentials")
