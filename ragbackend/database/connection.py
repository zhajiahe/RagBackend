import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Optional, Union

import asyncpg
import sqlalchemy
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine

from ragbackend import config

logger = logging.getLogger(__name__)


_pool: asyncpg.Pool | None = None


async def get_db_pool() -> asyncpg.Pool:
    """Get the pg connection pool."""
    global _pool
    if _pool is None:
        # Use parsed components for asyncpg connection
        _pool = await asyncpg.create_pool(
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            database=config.POSTGRES_DB,
        )
        logger.info("Database connection pool created using parsed URL components.")
    return _pool


async def close_db_pool():
    """Close the pg connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a connection from the pool."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            yield conn
        finally:
            await conn.close()


def get_vectorstore_engine(
    host: str = config.POSTGRES_HOST,
    port: str = config.POSTGRES_PORT,
    user: str = config.POSTGRES_USER,
    password: str = config.POSTGRES_PASSWORD,
    dbname: str = config.POSTGRES_DB,
) -> PGEngine:
    """Creates and returns a PGEngine for PostgreSQL with pgvector support."""
    # Updated connection string to use psycopg3 (psycopg://)
    connection_string = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
    engine = PGEngine.from_connection_string(url=connection_string)
    return engine


DBConnection = Union[sqlalchemy.engine.Engine, str]


async def get_vectorstore(
    collection_name: str = config.DEFAULT_COLLECTION_NAME,
    embeddings: Optional[Embeddings] = None,
    engine: Optional[PGEngine] = None,
    collection_metadata: Optional[dict[str, Any]] = None,
    vector_size: int = 512,
) -> PGVectorStore:
    """Initializes and returns a PGVectorStore for a specific collection,
    using an existing engine or creating one from connection parameters.
    """
    if engine is None:
        engine = get_vectorstore_engine()
    
    if embeddings is None:
        embeddings = config.get_default_embeddings()

    # Initialize the vectorstore table if it doesn't exist
    await engine.ainit_vectorstore_table(
        table_name=collection_name,
        vector_size=vector_size,
    )

    # Create the vectorstore using the new async PGVectorStore
    store = await PGVectorStore.create(
        engine=engine,
        table_name=collection_name,
        embedding_service=embeddings,
    )
    return store

