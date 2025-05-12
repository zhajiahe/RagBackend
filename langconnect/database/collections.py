import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from langconnect.auth import AuthenticatedUser
from langconnect.database.connection import get_db_connection, get_vectorstore
from langconnect.database.utils import assert_collection_owner

logger = logging.getLogger(__name__)


async def create_pgvector_collection(
    user: AuthenticatedUser, collection_name: str, metadata: dict[str, Any]
) -> None:
    """Explicitly creates a collection using PGVector with optional metadata.

    Note: This is often not necessary as adding documents implicitly creates it.
    PGVector.create_collection is synchronous, so run in executor.
    """
    if not isinstance(metadata, dict):
        raise TypeError(
            f"Programming error: metadata must be a dict. Got {type(metadata)}"
        )

    # The fields below are stored in the metadata column for now, but they
    # should be stored in separate columns.
    metadata["owner_id"] = user.identity
    # Write current time in ISO-8601 formatted style to created_at
    metadata["created_at"] = datetime.now(UTC).isoformat()

    # Calling this will create the collection w/ metadata in the database.
    # The PGVector class will always attempt to get/create a collection when
    # the class is instantiated.
    get_vectorstore(collection_name, collection_metadata=metadata)


async def list_pgvector_collections(user: AuthenticatedUser) -> list[dict[str, Any]]:
    """Lists all collections directly from the langchain_pg_collection table.

    Filters collections by matching the usowner_ider_id in the cmetadata JSONB field with the authenticated user's identity.
    """
    collections = []
    async with get_db_connection() as conn:
        query = """
            SELECT uuid, name, cmetadata
            FROM langchain_pg_collection 
            WHERE cmetadata->>'owner_id' = $1
            ORDER BY name;
        """
        records = await conn.fetch(query, user.identity)
        for record in records:
            # Handle cmetadata - it can be None, a string 'null', or a JSON string
            metadata = {}
            if record["cmetadata"] is not None and record["cmetadata"] != "null":
                try:
                    # If it's a JSON string, parse it
                    if isinstance(record["cmetadata"], str) and record[
                        "cmetadata"
                    ].startswith("{"):
                        metadata = json.loads(record["cmetadata"])
                    else:
                        metadata = record["cmetadata"]
                except Exception as e:
                    logger.exception(
                        f"Error parsing metadata in list_pgvector_collections: {e}"
                    )
                    # If parsing fails, use empty dict

            collection = {
                "uuid": str(record["uuid"]),
                "name": record["name"],
                "metadata": metadata,
            }
            collections.append(collection)
    return collections


async def get_pgvector_collection_details(
    user: AuthenticatedUser,
    collection_name: str,
) -> dict[str, Any] | None:
    """Gets collection details (uuid, name, metadata) from the langchain_pg_collection table.

    Filters collections by matching the owner_id in the cmetadata JSONB field with the authenticated user's identity.
    """
    async with get_db_connection() as conn:
        query = """
            SELECT uuid, name, cmetadata 
            FROM langchain_pg_collection 
            WHERE name = $1 AND cmetadata->>'owner_id' = $2;
        """
        record = await conn.fetchrow(query, collection_name, user.identity)
        if record:
            # Handle cmetadata - it can be None, a string 'null', or a JSON string
            metadata = {}
            if record["cmetadata"] is not None and record["cmetadata"] != "null":
                try:
                    # If it's a JSON string, parse it
                    if isinstance(record["cmetadata"], str) and record[
                        "cmetadata"
                    ].startswith("{"):
                        metadata = json.loads(record["cmetadata"])
                    else:
                        metadata = record["cmetadata"]
                except Exception as e:
                    logger.exception(
                        f"Error parsing metadata in get_pgvector_collection_details: {e}"
                    )
            return {
                "uuid": str(record["uuid"]),
                "name": record["name"],
                "metadata": metadata,
            }
    return None


async def delete_pgvector_collection(
    user: AuthenticatedUser, collection_name: str
) -> None:
    """Deletes a collection using PGVector.
    PGVector.delete_collection is synchronous, so run in executor.
    """
    store = get_vectorstore(collection_name)

    assert_collection_owner(store, user)

    await asyncio.to_thread(store.delete_collection)


async def update_pgvector_collection(
    collection_name: str,
    new_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Updates a collection's name and/or metadata in the langchain_pg_collection table.

    Args:
        collection_name: Current name of the collection to update
        new_name: Optional new name for the collection
        metadata: Optional new metadata to update or merge with existing metadata

    Returns:
        Updated collection details or None if collection not found

    """
    # First, get the existing collection to ensure it exists and to get current metadata
    existing_collection = await get_pgvector_collection_details(collection_name)
    if not existing_collection:
        return None

    # If no updates are provided, return the existing collection
    if new_name is None and metadata is None:
        return existing_collection

    # Prepare the update data
    update_name = new_name if new_name is not None else collection_name

    # For metadata, if provided, merge with existing metadata
    final_metadata = existing_collection["metadata"]
    if metadata is not None:
        # Update the existing metadata with new values
        final_metadata.update(metadata)

    # Convert metadata to JSON string for storage
    metadata_json = json.dumps(final_metadata) if final_metadata else None

    async with get_db_connection() as conn:
        query = """
            UPDATE langchain_pg_collection 
            SET name = $1, cmetadata = $2
            WHERE name = $3
            RETURNING uuid, name, cmetadata;
        """
        record = await conn.fetchrow(query, update_name, metadata_json, collection_name)

        if record:
            # Parse metadata from the result
            updated_metadata = {}
            if record["cmetadata"] is not None and record["cmetadata"] != "null":
                try:
                    if isinstance(record["cmetadata"], str) and record[
                        "cmetadata"
                    ].startswith("{"):
                        updated_metadata = json.loads(record["cmetadata"])
                    else:
                        updated_metadata = record["cmetadata"]
                except Exception as e:
                    logger.exception(
                        f"Error parsing metadata in update_pgvector_collection: {e}"
                    )

            return {
                "uuid": str(record["uuid"]),
                "name": record["name"],
                "metadata": updated_metadata,
            }

    return None
