import asyncpg
from typing import Dict, List, Optional, Any
from uuid import UUID
from ..models.collection import (
    CollectionCreate,
    CollectionUpdate,
)
from .connection import get_db_connection


# Helper to convert asyncpg.Record to dict, handling UUID and datetime
def record_to_dict(record: asyncpg.Record) -> Optional[Dict[str, Any]]:
    if record is None:
        return None
    return dict(record)


# =====================
# Collection DB Operations
# =====================


async def create_collection_in_db(collection_data: CollectionCreate) -> Dict[str, Any]:
    """Create a new collection in the database."""
    async with get_db_connection() as conn:
        query = """
            INSERT INTO collections (name, description)
            VALUES ($1, $2)
            RETURNING id, name, description, created_at, updated_at;
        """
        record = await conn.fetchrow(
            query, collection_data.name, collection_data.description
        )
    return record_to_dict(record)


async def list_collections_from_db() -> List[Dict[str, Any]]:
    """List all collections from the database."""
    async with get_db_connection() as conn:
        query = """
            SELECT id, name, description, created_at, updated_at
            FROM collections
            ORDER BY created_at DESC;
        """
        records = await conn.fetch(query)
    return [record_to_dict(r) for r in records]


async def get_collection_from_db(collection_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a collection from the database by ID."""
    async with get_db_connection() as conn:
        query = """
            SELECT id, name, description, created_at, updated_at
            FROM collections
            WHERE id = $1;
        """
        record = await conn.fetchrow(query, collection_id)
    return record_to_dict(record)


async def update_collection_in_db(
    collection_id: UUID, collection_data: CollectionUpdate
) -> Optional[Dict[str, Any]]:
    """Update a collection in the database."""
    # Build the SET part of the query dynamically
    update_fields = collection_data.model_dump(exclude_unset=True)
    if not update_fields:
        # If nothing to update, maybe fetch and return current state or raise error
        return await get_collection_from_db(collection_id)

    set_clauses = []
    values = []
    param_idx = 1
    for key, value in update_fields.items():
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1

    # Always update the timestamp
    set_clauses.append("updated_at = NOW()")
    values.append(collection_id)
    param_idx_id = param_idx

    query = f"""
        UPDATE collections
        SET {", ".join(set_clauses)}
        WHERE id = ${param_idx_id}
        RETURNING id, name, description, created_at, updated_at;
    """
    async with get_db_connection() as conn:
        record = await conn.fetchrow(query, *values)
    return record_to_dict(record)


async def delete_collection_from_db(collection_id: UUID) -> bool:
    """Delete a collection (and its documents) from the database."""
    async with get_db_connection() as conn:
        async with conn.transaction():
            # Optional: Delete associated documents first if FK constraint doesn't cascade
            # await conn.execute("DELETE FROM documents WHERE collection_id = $1", collection_id)

            query = """
                DELETE FROM collections
                WHERE id = $1;
            """
            status = await conn.execute(query, collection_id)
            # status is like 'DELETE 1' or 'DELETE 0'
            return status.split(" ")[1] == "1"
