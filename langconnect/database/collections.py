import json
import logging
import uuid
from typing import Any, NotRequired, Optional, TypedDict

from fastapi import status
from fastapi.exceptions import HTTPException

from langconnect.database.connection import get_db_connection, get_vectorstore

logger = logging.getLogger(__name__)


class CollectionDetails(TypedDict):
    """TypedDict for collection details."""

    uuid: str
    name: str
    metadata: dict[str, Any]
    # Temporary field used internally to work-around an issue with PGVector
    table_id: NotRequired[str]


class Collections:
    """Manages pgvector-backed collections, with user_id passed at runtime."""

    async def list(
        self,
        user_id: str,
    ) -> list[CollectionDetails]:
        """List all collections owned by the given user, ordered by logical name."""
        async with get_db_connection() as conn:
            records = await conn.fetch(
                """
                SELECT uuid, cmetadata
                FROM langchain_pg_collection
                WHERE cmetadata->>'owner_id' = $1
                ORDER BY cmetadata->>'name';
                """,
                user_id,
            )

        result: list[CollectionDetails] = []
        for r in records:
            metadata = json.loads(r["cmetadata"])
            name = metadata.pop("name", "Unnamed")
            result.append(
                {
                    "uuid": str(r["uuid"]),
                    "name": name,
                    "metadata": metadata,
                }
            )
        return result

    async def get(
        self,
        user_id: str,
        collection_id: str,
    ) -> CollectionDetails | None:
        """Fetch a single collection by UUID, ensuring the user owns it."""
        async with get_db_connection() as conn:
            rec = await conn.fetchrow(
                """
                SELECT uuid, name, cmetadata
                  FROM langchain_pg_collection
                 WHERE uuid = $1
                   AND cmetadata->>'owner_id' = $2;
                """,
                collection_id,
                user_id,
            )

        if not rec:
            return None

        metadata = json.loads(rec["cmetadata"])
        name = metadata.pop("name", "Unnamed")
        return {
            "uuid": str(rec["uuid"]),
            "name": name,
            "metadata": metadata,
            "table_id": rec["name"],
        }

    async def create(
        self,
        user_id: str,
        collection_name: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> CollectionDetails | None:
        """Create a new collection.

        Args:
            user_id: The ID of the user creating the collection.
            collection_name: The name of the new collection.
            metadata: Optional metadata for the collection.

        Returns:
            Details of the created collection or None if creation failed.
        """
        # check for existing name
        metadata = metadata.copy() if metadata else {}
        metadata["owner_id"] = user_id
        metadata["name"] = collection_name

        # For now just assign a random table id
        table_id = str(uuid.uuid4())

        # triggers PGVector to create both the vectorstore and DB entry
        get_vectorstore(table_id, collection_metadata=metadata)

        # Fetch the newly created table.
        async with get_db_connection() as conn:
            rec = await conn.fetchrow(
                """
                SELECT uuid, name, cmetadata
                  FROM langchain_pg_collection
                 WHERE name = $1
                   AND cmetadata->>'owner_id' = $2;
                """,
                table_id,
                user_id,
            )
        if not rec:
            return None
        metadata = json.loads(rec["cmetadata"])
        name = metadata.pop("name")
        return {"uuid": str(rec["uuid"]), "name": name, "metadata": metadata}

    async def update(
        self,
        user_id: str,
        collection_id: str,
        *,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> CollectionDetails:
        """Update collection metadata.

        Four cases:

        1) metadata only          → merge in metadata, keep old JSON->'name'
        2) metadata + new name    → merge metadata (including new 'name')
        3) new name only          → jsonb_set the 'name' key
        4) neither                → no-op, just fetch & return
        """
        # Case 4: no-op
        if metadata is None and name is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must update at least 1 attribute.",
            )

        # Case 1 & 2: metadata supplied (with or without new name)
        if metadata is not None:
            # merge in owner_id + optional new name
            merged = metadata.copy()
            merged["owner_id"] = user_id

            if name is not None:
                merged["name"] = name
            else:
                # pull existing friendly name so we don't lose it
                existing = await self.get(user_id, collection_id)
                if not existing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Collection '{collection_id}' not found or not owned by you.",
                    )
                merged["name"] = existing["name"]

            metadata_json = json.dumps(merged)

            async with get_db_connection() as conn:
                rec = await conn.fetchrow(
                    """
                    UPDATE langchain_pg_collection
                       SET cmetadata = $1::jsonb
                     WHERE uuid = $2
                       AND cmetadata->>'owner_id' = $3
                    RETURNING uuid, cmetadata;
                    """,
                    metadata_json,
                    collection_id,
                    user_id,
                )

        # Case 3: name only
        else:  # metadata is None but name is not None
            async with get_db_connection() as conn:
                rec = await conn.fetchrow(
                    """
                    UPDATE langchain_pg_collection
                       SET cmetadata = jsonb_set(
                             cmetadata::jsonb,
                             '{name}',
                             to_jsonb($1::text),
                             true
                           )
                     WHERE uuid = $2
                       AND cmetadata->>'owner_id' = $3
                    RETURNING uuid, cmetadata;
                    """,
                    name,
                    collection_id,
                    user_id,
                )

        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection_id}' not found or not owned by you.",
            )

        full_meta = json.loads(rec["cmetadata"])
        friendly_name = full_meta.pop("name", "Unnamed")

        return {
            "uuid": str(rec["uuid"]),
            "name": friendly_name,
            "metadata": full_meta,
        }

    async def delete(
        self,
        user_id: str,
        collection_id: str,
    ) -> int:
        """Delete a collection by UUID.
        Returns number of rows deleted (1).
        Raises 404 if no such collection.
        """
        async with get_db_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM langchain_pg_collection
                 WHERE uuid = $1
                   AND cmetadata->>'owner_id' = $2;
                """,
                collection_id,
                user_id,
            )
        return int(result.split()[-1])


# Singleton collections object.
COLLECTIONS = Collections()
