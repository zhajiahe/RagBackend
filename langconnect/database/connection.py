import os
import asyncpg
from langchain_postgres.vectorstores import ConnectionOptions
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# PgVector Configuration
CONNECTION_OPTIONS = ConnectionOptions(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=int(os.environ.get("POSTGRES_PORT", "5432")),  # Ensure port is int
    user=os.environ.get("POSTGRES_USER", "postgres"),
    password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    database=os.environ.get("POSTGRES_DB", "postgres"),
)

_pool: asyncpg.Pool = None


async def get_db_pool() -> asyncpg.Pool:
    """Get the asyncpg connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                user=CONNECTION_OPTIONS.user,
                password=CONNECTION_OPTIONS.password,
                database=CONNECTION_OPTIONS.database,
                host=CONNECTION_OPTIONS.host,
                port=CONNECTION_OPTIONS.port,
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


# Keep the old function signature for compatibility if needed, but prefer the pool
async def get_db_connection_options() -> ConnectionOptions:
    """Get the connection options (legacy)."""
    return CONNECTION_OPTIONS
