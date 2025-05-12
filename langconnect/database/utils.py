from langchain_postgres.vectorstores import PGVector

from langconnect.auth import AuthenticatedUser


def assert_collection_owner(store: PGVector, user: AuthenticatedUser) -> None:
    """Asserts that the collection belongs to the user."""
    if store.collection_metadata is None:
        raise ValueError("Collection metadata not found")
    if store.collection_metadata["owner_id"] != user.identity:
        raise ValueError("User does not own the collection")
