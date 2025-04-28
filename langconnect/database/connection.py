import os
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlparse, urlunparse

from langchain_postgres.vectorstores import PGVector
from langchain_core.embeddings import Embeddings
from ..defaults import DEFAULT_EMBEDDINGS, DEFAULT_COLLECTION_NAME

_pool: asyncpg.Pool = None

# --- Configuration ---
POSTGRES_URL = os.getenv("POSTGRES_URL")
ASYNC_PG_DSN: str
SQLALCHEMY_ASYNC_CONN_STR: str

if POSTGRES_URL:
    # Use POSTGRES_URL if available
    print(f"Using POSTGRES_URL: {POSTGRES_URL}")
    ASYNC_PG_DSN = POSTGRES_URL

    # Derive SQLAlchemy-style async connection string from POSTGRES_URL
    parsed_url = urlparse(POSTGRES_URL)
    if parsed_url.scheme not in ("postgresql", "postgres"):
        # asyncpg might handle 'postgres', but SQLAlchemy needs 'postgresql+driver'
        # For consistency, we'll require 'postgresql' if POSTGRES_URL is set.
        raise ValueError(
            f"POSTGRES_URL must start with 'postgresql://' or 'postgres://', found: {parsed_url.scheme}"
        )
    sql_alchemy_url_parts = list(parsed_url)
    # Ensure scheme is 'postgresql+asyncpg' for SQLAlchemy
    sql_alchemy_url_parts[0] = "postgresql+asyncpg"
    SQLALCHEMY_ASYNC_CONN_STR = urlunparse(sql_alchemy_url_parts)

else:
    # Fallback to individual environment variables (original logic)
    print(
        "POSTGRES_URL not set, constructing connection strings from individual variables."
    )
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    DB_NAME = os.getenv("POSTGRES_DB", "langconnect_dev")

    # Construct DSN for asyncpg (needs postgres:// scheme)
    ASYNC_PG_DSN = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # Construct SQLAlchemy-style async connection string (needs postgresql+asyncpg://)
    SQLALCHEMY_ASYNC_CONN_STR = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

# --- Helper Functions ---


async def get_db_pool() -> asyncpg.Pool:
    """Get the asyncpg connection pool."""
    global _pool
    if _pool is None:
        try:
            # Use the determined DSN string for asyncpg
            _pool = await asyncpg.create_pool(
                dsn=ASYNC_PG_DSN,
                # Add other pool options if needed, e.g., min_size, max_size
            )
            print("Database connection pool created.")
        except Exception as e:
            print(f"Error creating database connection pool: {e}")
            raise
    return _pool


async def close_db_pool():
    """Close the asyncpg connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        print("Database connection pool closed.")


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a connection from the pool."""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection


def get_vectorstore(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embeddings: Embeddings = DEFAULT_EMBEDDINGS,
    # Use the determined SQLAlchemy-style async connection string
    connection_string: str = SQLALCHEMY_ASYNC_CONN_STR,
) -> PGVector:
    """Initializes and returns a PGVector store for a specific collection."""
    # PGVector infers async mode from 'postgresql+asyncpg' driver in connection string
    store = PGVector(
        embeddings,
        collection_name=collection_name,
        connection=connection_string,
    )
    return store
