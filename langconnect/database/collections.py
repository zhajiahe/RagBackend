import asyncio
import json
from typing import Dict, List, Optional, Any


from .connection import get_db_connection, get_vectorstore


def create_pgvector_collection(
    collection_name: str, metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Explicitly creates a collection using PGVector with optional metadata.
    Note: This is often not necessary as adding documents implicitly creates it.
    PGVector.create_collection is synchronous, so run in executor."""
    # Calling this will create the collection w/ metadata in the database.
    # The PGVector class will always attempt to get/create a collection when
    # the class is instantiated.
    get_vectorstore(collection_name, collection_metadata=metadata)


async def list_pgvector_collections() -> List[Dict[str, Any]]:
    """Lists all collections directly from the langchain_pg_collection table."""
    collections = []
    async with get_db_connection() as conn:
        query = """
            SELECT uuid, name, cmetadata FROM langchain_pg_collection ORDER BY name;
        """
        records = await conn.fetch(query)
        for record in records:
            print(f"Found collection: {record}")
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
                    print(f"Error parsing metadata in list_pgvector_collections: {e}")
                    # If parsing fails, use empty dict

            collection = {
                "uuid": str(record["uuid"]),
                "name": record["name"],
                "metadata": metadata,
            }
            collections.append(collection)
    return collections


async def get_pgvector_collection_details(
    collection_name: str,
) -> Optional[Dict[str, Any]]:
    """Gets collection details (uuid, name, metadata) from the langchain_pg_collection table."""
    async with get_db_connection() as conn:
        query = """
            SELECT uuid, name, cmetadata FROM langchain_pg_collection WHERE name = $1;
        """
        record = await conn.fetchrow(query, collection_name)
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
                    print(
                        f"Error parsing metadata in get_pgvector_collection_details: {e}"
                    )
                    # If parsing fails, use empty dict

            return {
                "uuid": str(record["uuid"]),
                "name": record["name"],
                "metadata": metadata,
            }
    return None


async def delete_pgvector_collection(collection_name: str) -> None:
    """Deletes a collection using PGVector.
    PGVector.delete_collection is synchronous, so run in executor."""
    store = get_vectorstore(collection_name)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, store.delete_collection)
