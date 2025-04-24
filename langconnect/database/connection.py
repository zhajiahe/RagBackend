import os
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# PgVector Configuration removed - read directly from env vars

_pool: asyncpg.Pool = None


async def get_db_pool() -> asyncpg.Pool:
    """Get the asyncpg connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                user=os.environ.get("POSTGRES_USER", "postgres"),
                password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
                database=os.environ.get("POSTGRES_DB", "postgres"),
                host=os.environ.get("POSTGRES_HOST", "localhost"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),  # Ensure port is int
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
