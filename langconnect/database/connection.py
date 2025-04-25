import os
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from langchain_postgres.vectorstores import PGVector
from langchain_core.embeddings import Embeddings
from ..defaults import DEFAULT_EMBEDDINGS, DEFAULT_COLLECTION_NAME

# PgVector Configuration removed - read directly from env vars

_pool: asyncpg.Pool = None

# --- Configuration ---
# Construct connection string from environment variables set by docker-compose
DB_HOST = os.getenv(
    "POSTGRES_HOST", "localhost"
)  # Default for local dev outside docker
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")  # Default for local dev
DB_NAME = os.getenv("POSTGRES_DB", "langconnect_dev")  # Default for local dev

CONNECTION_STRING = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
ASYNC_CONNECTION_STRING = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- Helper Functions ---


async def get_db_pool() -> asyncpg.Pool:
    """Get the asyncpg connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                host=DB_HOST,
                port=int(DB_PORT),  # Ensure port is int
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
    connection_string: str = CONNECTION_STRING,
    # mode: str = "async", # langchain-postgres handles async based on driver in conn string
) -> PGVector:
    """Initializes and returns a PGVector store for a specific collection."""
    # Consider adding error handling for connection issues
    store = PGVector(
        embeddings,
        collection_name=collection_name,
        connection=connection_string,  # Use connection string directly
        async_mode=connection_string == ASYNC_CONNECTION_STRING,
        # use_jsonb=True # Store metadata in JSONB - should be default now
    )
    return store
