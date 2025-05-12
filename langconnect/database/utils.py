from fastapi.exceptions import HTTPException
from langchain_postgres.vectorstores import PGVector

from langconnect.auth import AuthenticatedUser


def assert_collection_owner(store: PGVector, user: AuthenticatedUser) -> None:
    """Asserts that the collection belongs to the user."""
    metadata = store.collection_metadata or {}
    owner_id = metadata.get("owner_id")
    # Careful to return 404 to avoid leaking information about collections
    # existing for other users.
    if not owner_id or owner_id != user.identity:
        raise HTTPException(status_code=404, detail="Collection does not exist.")
