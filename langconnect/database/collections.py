import asyncio
from typing import Dict, List, Optional, Any

from langchain_core.embeddings import Embeddings
from langchain_postgres.vectorstores import PGVector

import os
from langchain_openai import OpenAIEmbeddings

from .connection import get_db_connection

CONNECTION_STRING = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/langconnect_dev",
)
DEFAULT_EMBEDDINGS = OpenAIEmbeddings()


def get_vectorstore_for_collection_management(
    collection_name: str,
    embeddings: Embeddings = DEFAULT_EMBEDDINGS,
    connection_string: str = CONNECTION_STRING,
) -> PGVector:
    """Initializes and returns a PGVector store for managing a specific collection."""
    store = PGVector(
        collection_name=collection_name,
        connection=connection_string,
        embeddings=embeddings,
    )
    return store


async def create_pgvector_collection(collection_name: str) -> None:
    """Explicitly creates a collection using PGVector.
    Note: This is often not necessary as adding documents implicitly creates it.
    PGVector.create_collection is synchronous, so run in executor."""
    store = get_vectorstore_for_collection_management(collection_name)
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
    store = get_vectorstore_for_collection_management(collection_name)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, store.delete_collection)
