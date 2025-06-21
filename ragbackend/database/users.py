"""User database operations."""

import asyncpg
import logging
from datetime import datetime
from typing import Optional
import uuid

from ragbackend.database.connection import get_db_connection

logger = logging.getLogger(__name__)


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


async def create_default_admin_user():
    """Create default admin user if it doesn't exist and password is provided."""
    from ragbackend import config
    from ragbackend.services.jwt_service import get_password_hash
    
    # Skip if no admin password is configured
    if not config.DEFAULT_ADMIN_PASSWORD:
        logger.info("No default admin password configured, skipping admin user creation")
        return
    
    try:
        # Check if admin user already exists
        existing_user = await get_user_by_username(config.DEFAULT_ADMIN_USERNAME)
        if existing_user:
            logger.info(f"Admin user '{config.DEFAULT_ADMIN_USERNAME}' already exists")
            return
        
        # Check if admin email already exists
        existing_email = await get_user_by_email(config.DEFAULT_ADMIN_EMAIL)
        if existing_email:
            logger.warning(f"Email '{config.DEFAULT_ADMIN_EMAIL}' already exists, skipping admin user creation")
            return
        
        # Create admin user
        hashed_password = get_password_hash(config.DEFAULT_ADMIN_PASSWORD)
        admin_user = await create_user(
            email=config.DEFAULT_ADMIN_EMAIL,
            username=config.DEFAULT_ADMIN_USERNAME,
            hashed_password=hashed_password,
            full_name=config.DEFAULT_ADMIN_FULL_NAME
        )
        
        logger.info(f"Default admin user '{config.DEFAULT_ADMIN_USERNAME}' created successfully")
        return admin_user
        
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        raise 