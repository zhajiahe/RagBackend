"""User database operations."""

import asyncpg
from datetime import datetime
from typing import Optional
import uuid

from ragbackend.database.connection import get_db_connection


async def create_users_table():
    """Create the users table if it doesn't exist."""
    async with get_db_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                full_name VARCHAR(255),
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        """)


async def create_user(
    email: str,
    username: str,
    hashed_password: str,
    full_name: Optional[str] = None
) -> dict:
    """Create a new user in the database."""
    async with get_db_connection() as conn:
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        result = await conn.fetchrow("""
            INSERT INTO users (id, email, username, full_name, hashed_password, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, email, username, full_name, is_active, created_at, updated_at
        """, user_id, email, username, full_name, hashed_password, now, now)
        
        return dict(result)


async def get_user_by_username(username: str) -> Optional[dict]:
    """Get a user by username."""
    async with get_db_connection() as conn:
        result = await conn.fetchrow("""
            SELECT id, email, username, full_name, hashed_password, is_active, created_at, updated_at
            FROM users 
            WHERE username = $1
        """, username)
        
        return dict(result) if result else None


async def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by email."""
    async with get_db_connection() as conn:
        result = await conn.fetchrow("""
            SELECT id, email, username, full_name, hashed_password, is_active, created_at, updated_at
            FROM users 
            WHERE email = $1
        """, email)
        
        return dict(result) if result else None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get a user by ID."""
    async with get_db_connection() as conn:
        result = await conn.fetchrow("""
            SELECT id, email, username, full_name, hashed_password, is_active, created_at, updated_at
            FROM users 
            WHERE id = $1
        """, user_id)
        
        return dict(result) if result else None


async def update_user_last_login(user_id: str):
    """Update user's last login timestamp."""
    async with get_db_connection() as conn:
        await conn.execute("""
            UPDATE users 
            SET updated_at = NOW()
            WHERE id = $1
        """, user_id) 