"""File metadata management for MinIO integration."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from ragbackend.database.connection import get_db_connection

logger = logging.getLogger(__name__)


async def create_files_table() -> bool:
    """Create the files metadata table if it doesn't exist."""
    try:
        async with get_db_connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS file_storage (
                    id SERIAL PRIMARY KEY,
                    file_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    collection_id VARCHAR(255) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    content_type VARCHAR(100),
                    file_size BIGINT NOT NULL,
                    object_path VARCHAR(500) UNIQUE NOT NULL,
                    bucket_name VARCHAR(100) NOT NULL,
                    etag VARCHAR(255),
                    metadata JSONB DEFAULT '{}',
                    upload_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_storage_user_id 
                ON file_storage(user_id);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_storage_collection_id 
                ON file_storage(collection_id);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_storage_file_id 
                ON file_storage(file_id);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_storage_user_collection 
                ON file_storage(user_id, collection_id);
            """)
            
            logger.info("Files metadata table created successfully.")
            return True
            
    except Exception as e:
        logger.error(f"Failed to create files metadata table: {e}")
        return False


async def insert_file_metadata(file_metadata: Dict[str, Any]) -> Optional[int]:
    """
    Insert file metadata into the database.
    
    Args:
        file_metadata: Dictionary containing file metadata
        
    Returns:
        The inserted record ID or None if failed
    """
    try:
        async with get_db_connection() as conn:
            query = """
                INSERT INTO file_storage (
                    file_id, user_id, collection_id, filename, original_filename,
                    content_type, file_size, object_path, bucket_name, etag, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id;
            """
            
            result = await conn.fetchrow(
                query,
                file_metadata['file_id'],
                file_metadata['user_id'],
                file_metadata['collection_id'],
                file_metadata['filename'],
                file_metadata.get('original_filename', file_metadata['filename']),
                file_metadata.get('content_type'),
                file_metadata['size'],
                file_metadata['object_path'],
                file_metadata['bucket'],
                file_metadata.get('etag'),
                json.dumps(file_metadata.get('metadata', {}))
            )
            
            if result:
                logger.info(f"File metadata inserted with ID: {result['id']}")
                return result['id']
            
    except Exception as e:
        logger.error(f"Failed to insert file metadata: {e}")
        return None


async def get_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get file metadata by file_id.
    
    Args:
        file_id: The unique file identifier
        
    Returns:
        File metadata dictionary or None if not found
    """
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT * FROM file_storage WHERE file_id = $1;
            """
            
            result = await conn.fetchrow(query, file_id)
            
            if result:
                return dict(result)
            
    except Exception as e:
        logger.error(f"Failed to get file metadata for {file_id}: {e}")
        return None


async def get_files_by_collection(
    collection_id: str, 
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get all files for a specific collection and user.
    
    Args:
        collection_id: Collection identifier
        user_id: User identifier
        limit: Maximum number of files to return
        offset: Number of files to skip
        
    Returns:
        List of file metadata dictionaries
    """
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT * FROM file_storage 
                WHERE collection_id = $1 AND user_id = $2
                ORDER BY upload_time DESC
                LIMIT $3 OFFSET $4;
            """
            
            results = await conn.fetch(query, collection_id, user_id, limit, offset)
            
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Failed to get files for collection {collection_id}: {e}")
        return []


async def get_files_by_user(
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get all files for a specific user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of files to return
        offset: Number of files to skip
        
    Returns:
        List of file metadata dictionaries
    """
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT * FROM file_storage 
                WHERE user_id = $1
                ORDER BY upload_time DESC
                LIMIT $2 OFFSET $3;
            """
            
            results = await conn.fetch(query, user_id, limit, offset)
            
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Failed to get files for user {user_id}: {e}")
        return []


async def delete_file_metadata(file_id: str) -> bool:
    """
    Delete file metadata from the database.
    
    Args:
        file_id: The unique file identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        async with get_db_connection() as conn:
            query = "DELETE FROM file_storage WHERE file_id = $1;"
            
            result = await conn.execute(query, file_id)
            
            # Check if any rows were affected
            if result == "DELETE 1":
                logger.info(f"File metadata deleted for file_id: {file_id}")
                return True
            else:
                logger.warning(f"No file metadata found for file_id: {file_id}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to delete file metadata for {file_id}: {e}")
        return False


async def delete_files_by_collection(collection_id: str, user_id: str) -> int:
    """
    Delete all file metadata for a specific collection and user.
    
    Args:
        collection_id: Collection identifier
        user_id: User identifier
        
    Returns:
        Number of files deleted
    """
    try:
        async with get_db_connection() as conn:
            # First get the list of files to be deleted for logging
            select_query = """
                SELECT file_id, object_path FROM file_storage 
                WHERE collection_id = $1 AND user_id = $2;
            """
            
            files_to_delete = await conn.fetch(select_query, collection_id, user_id)
            
            # Delete the files
            delete_query = """
                DELETE FROM file_storage 
                WHERE collection_id = $1 AND user_id = $2;
            """
            
            result = await conn.execute(delete_query, collection_id, user_id)
            
            # Extract the number of deleted rows from the result
            deleted_count = int(result.split()[-1]) if result.startswith("DELETE") else 0
            
            logger.info(f"Deleted {deleted_count} file metadata records for collection {collection_id}")
            
            return deleted_count
            
    except Exception as e:
        logger.error(f"Failed to delete files for collection {collection_id}: {e}")
        return 0


async def update_file_metadata(
    file_id: str, 
    updates: Dict[str, Any]
) -> bool:
    """
    Update file metadata.
    
    Args:
        file_id: The unique file identifier
        updates: Dictionary of fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not updates:
            return True
            
        async with get_db_connection() as conn:
            # Build the update query dynamically
            set_clauses = []
            values = []
            param_count = 1
            
            for key, value in updates.items():
                if key in ['filename', 'content_type', 'file_size', 'metadata']:
                    set_clauses.append(f"{key} = ${param_count}")
                    values.append(value if key != 'metadata' else json.dumps(value))
                    param_count += 1
            
            if not set_clauses:
                return True
                
            # Add updated_at timestamp
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
            
            # Add file_id for WHERE clause
            values.append(file_id)
            
            query = f"""
                UPDATE file_storage 
                SET {', '.join(set_clauses)}
                WHERE file_id = ${param_count};
            """
            
            result = await conn.execute(query, *values)
            
            if result == "UPDATE 1":
                logger.info(f"File metadata updated for file_id: {file_id}")
                return True
            else:
                logger.warning(f"No file metadata found for file_id: {file_id}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to update file metadata for {file_id}: {e}")
        return False


async def get_file_count_by_collection(collection_id: str, user_id: str) -> int:
    """
    Get the total number of files in a collection for a user.
    
    Args:
        collection_id: Collection identifier
        user_id: User identifier
        
    Returns:
        Number of files in the collection
    """
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT COUNT(*) as count FROM file_storage 
                WHERE collection_id = $1 AND user_id = $2;
            """
            
            result = await conn.fetchrow(query, collection_id, user_id)
            
            return result['count'] if result else 0
            
    except Exception as e:
        logger.error(f"Failed to get file count for collection {collection_id}: {e}")
        return 0


async def get_total_file_size_by_user(user_id: str) -> int:
    """
    Get the total file size for all files owned by a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Total file size in bytes
    """
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT COALESCE(SUM(file_size), 0) as total_size 
                FROM file_storage WHERE user_id = $1;
            """
            
            result = await conn.fetchrow(query, user_id)
            
            return result['total_size'] if result else 0
            
    except Exception as e:
        logger.error(f"Failed to get total file size for user {user_id}: {e}")
        return 0 