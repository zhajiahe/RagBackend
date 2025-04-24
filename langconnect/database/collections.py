import asyncio
from typing import Dict, List, Optional, Any



from .connection import get_db_connection, get_vectorstore


async def create_pgvector_collection(collection_name: str) -> None:
    """Explicitly creates a collection using PGVector.
    Note: This is often not necessary as adding documents implicitly creates it.
    PGVector.create_collection is synchronous, so run in executor."""
    store = get_vectorstore(collection_name)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, store.create_collection)


async def list_pgvector_collections() -> List[Dict[str, Any]]:
    """Lists all collections directly from the langchain_pg_collection table."""
    collections = []
    async with get_db_connection() as conn:
        query = """
            SELECT uuid, name, cmetadata FROM langchain_pg_collection ORDER BY name;
        """
        records = await conn.fetch(query)
        for record in records:
            collections.append({"uuid": str(record["uuid"]), "name": record["name"]})
    return collections


async def get_pgvector_collection_details(
    collection_name: str,
) -> Optional[Dict[str, Any]]:
    """Gets collection details (uuid, name) from the langchain_pg_collection table."""
    async with get_db_connection() as conn:
        query = """
            SELECT uuid, name FROM langchain_pg_collection WHERE name = $1;
        """
        record = await conn.fetchrow(query, collection_name)
        if record:
            return {"uuid": str(record["uuid"]), "name": record["name"]}
    return None


async def delete_pgvector_collection(collection_name: str) -> None:
    """Deletes a collection using PGVector.
    PGVector.delete_collection is synchronous, so run in executor."""
    store = get_vectorstore(collection_name)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, store.delete_collection)
