"""Module defines CollectionManager and Collection classes.

1. CollectionManager: for managing collections of documents in a database.
2. Collection: for managing the contents of a specific collection.

The current implementations are based on langchain-postgres AsyncPGVectorStore class.

Replace with your own implementation or favorite vectorstore if needed.
"""

import builtins
import json
import logging
import uuid
from typing import Any, NotRequired, Optional, TypedDict

from fastapi import status
from fastapi.exceptions import HTTPException
from langchain_core.documents import Document

from ragbackend.database.connection import get_db_connection, get_vectorstore_engine, get_vectorstore

logger = logging.getLogger(__name__)


class CollectionDetails(TypedDict):
    """TypedDict for collection details."""

    name: str
    uuid: str
    table_id: str
    metadata: dict[str, Any]
    embedding_model: str
    embedding_dimensions: NotRequired[int]


class DocumentUpdate(TypedDict):
    """TypedDict for document updates."""

    page_content: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class Collection:
    """Manages a vector-based collection of documents."""

    def __init__(self, collection_id: str, user_id: str, details: Optional[CollectionDetails] = None):
        """Initialize Collection with collection and user IDs."""
        self.collection_id = collection_id
        self.user_id = user_id
        self._details = details
        
        # If we don't have details, we'll fetch them when needed
        if not self._details:
            self._details = None

    @property
    def details(self) -> CollectionDetails:
        """Return collection details."""
        if self._details is None:
            # Fetch details from database if not already loaded
            raise RuntimeError("Collection details not loaded. Use CollectionManager.get_collection() to get a fully loaded Collection.")
        return self._details
    
    async def _load_details(self):
        """Load collection details from database."""
        manager = CollectionManager()
        collection = await manager.get_collection(self.collection_id)
        self._details = collection._details

    async def similarity_search(
        self,
        query: str,
        *,
        k: int = 4,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[Document]:
        """Perform similarity search."""
        from ragbackend import config

        if not self._details:
            await self._load_details()
        
        embeddings = config.get_default_embeddings()
        store = await get_vectorstore(collection_name=self._details["table_id"])
        return await store.asimilarity_search(query, k=k, filter=filter)

    async def similarity_search_with_score(
        self,
        query: str,
        *,
        k: int = 4,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[tuple[Document, float]]:
        """Perform similarity search with scores."""
        from ragbackend import config

        if not self._details:
            await self._load_details()

        embeddings = config.get_default_embeddings()
        store = await get_vectorstore(collection_name=self._details["table_id"])
        return await store.asimilarity_search_with_score(query, k=k, filter=filter)

    async def add_documents(self, docs: list[Document]) -> list[str]:
        """Add documents to collection."""
        if not self._details:
            await self._load_details()
        store = await get_vectorstore(collection_name=self._details["table_id"])
        return await store.aadd_documents(docs)

    async def get_documents(
        self,
        ids: Optional[list[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[Document]:
        """Get documents from collection."""
        if not self._details:
            await self._load_details()
        store = await get_vectorstore(collection_name=self._details["table_id"])
        
        # Use the collection method to get documents
        if ids:
            # Get specific documents by IDs
            return await store.aget_by_ids(ids)
        else:
            # Get all documents with pagination
            # Note: This is a simplified approach, actual implementation may vary
            # based on the specific AsyncPGVectorStore API
            all_docs = []
            try:
                # Try to use a search with very broad criteria to get all documents
                # This is a workaround since AsyncPGVectorStore might not have a direct "get all" method
                async with get_db_connection() as conn:
                    table_name = self._details["table_id"]
                    
                    # Build query with pagination
                    query = f"""
                        SELECT id, document, cmetadata, custom_id
                        FROM vectorstore_{table_name}
                        ORDER BY id
                        OFFSET $1
                    """
                    
                    if limit:
                        query += " LIMIT $2"
                        rows = await conn.fetch(query, offset, limit)
                    else:
                        rows = await conn.fetch(query, offset)
                    
                    for row in rows:
                        doc_data = json.loads(row["document"]) if isinstance(row["document"], str) else row["document"]
                        metadata = json.loads(row["cmetadata"]) if isinstance(row["cmetadata"], str) else row["cmetadata"] or {}
                        metadata["custom_id"] = row["custom_id"]
                        
                        doc = Document(
                            page_content=doc_data.get("page_content", ""),
                            metadata=metadata
                        )
                        all_docs.append(doc)
                        
            except Exception as e:
                logger.error(f"Error getting documents: {e}")
                # Fallback to empty list
                return []
                
            return all_docs

    async def update_document(self, doc_id: str, update: DocumentUpdate) -> bool:
        """Update a document in the collection."""
        try:
            if not self._details:
                await self._load_details()
            async with get_db_connection() as conn:
                table_name = self._details["table_id"]
                
                # First, get the existing document
                existing_row = await conn.fetchrow(
                    f"SELECT document, cmetadata FROM vectorstore_{table_name} WHERE custom_id = $1",
                    doc_id
                )
                
                if not existing_row:
                    return False
                
                # Parse existing data
                existing_doc = json.loads(existing_row["document"]) if isinstance(existing_row["document"], str) else existing_row["document"]
                existing_metadata = json.loads(existing_row["cmetadata"]) if isinstance(existing_row["cmetadata"], str) else existing_row["cmetadata"] or {}
                
                # Apply updates
                if "page_content" in update:
                    existing_doc["page_content"] = update["page_content"]
                
                if "metadata" in update:
                    existing_metadata.update(update["metadata"])
                
                # Update in database
                await conn.execute(
                    f"""
                    UPDATE vectorstore_{table_name}
                    SET document = $1, cmetadata = $2
                    WHERE custom_id = $3
                    """,
                    json.dumps(existing_doc),
                    json.dumps(existing_metadata),
                    doc_id
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False

    async def delete_documents(self, ids: list[str]) -> bool:
        """Delete documents from collection."""
        try:
            if not self._details:
                await self._load_details()
            store = await get_vectorstore(collection_name=self._details["table_id"])
            await store.adelete(ids)
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False

    async def count_documents(self) -> int:
        """Count documents in collection."""
        try:
            if not self._details:
                await self._load_details()
            async with get_db_connection() as conn:
                table_name = self._details["table_id"]
                result = await conn.fetchval(f"SELECT COUNT(*) FROM vectorstore_{table_name}")
                return result or 0
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    async def upsert(self, docs: list[Document]) -> list[str]:
        """Add documents to collection (alias for add_documents for API compatibility)."""
        return await self.add_documents(docs)
    
    async def delete(self, file_id: str) -> bool:
        """Delete documents by file_id and clean up MinIO files."""
        try:
            # First, get all documents with this file_id to find their IDs
            if not self._details:
                await self._load_details()
                
            async with get_db_connection() as conn:
                table_name = self._details["table_id"]
                
                # Find all document IDs with this file_id
                doc_rows = await conn.fetch(
                    f"""
                    SELECT custom_id FROM vectorstore_{table_name}
                    WHERE cmetadata->>'file_id' = $1
                    """,
                    file_id
                )
                
                if not doc_rows:
                    logger.warning(f"No documents found with file_id: {file_id}")
                    return False
                
                doc_ids = [row['custom_id'] for row in doc_rows]
                
                # Delete from vector store
                success = await self.delete_documents(doc_ids)
                
                if success:
                    # Delete from MinIO and file metadata
                    from ragbackend.services.minio_service import get_minio_service
                    from ragbackend.database.files import get_file_metadata, delete_file_metadata
                    
                    try:
                        # Get file metadata to find MinIO object path
                        file_metadata = await get_file_metadata(file_id)
                        if file_metadata:
                            # Delete from MinIO
                            minio_service = get_minio_service()
                            await minio_service.delete_file(file_metadata['object_path'])
                            
                            # Delete file metadata from database
                            await delete_file_metadata(file_id)
                            
                            logger.info(f"Successfully deleted file {file_id} from collection {self.collection_id}")
                        else:
                            logger.warning(f"No file metadata found for file_id: {file_id}")
                            
                    except Exception as e:
                        logger.error(f"Failed to clean up MinIO file {file_id}: {e}")
                        # Document deletion was successful, so we still return True
                
                return success
                
        except Exception as e:
            logger.error(f"Error deleting documents with file_id {file_id}: {e}")
            return False
    
    async def search(self, query: str, limit: int = 10) -> list:
        """Search for documents in the collection."""
        try:
            # Perform similarity search
            search_results = await self.similarity_search_with_score(query, k=limit)
            
            # Format results for API response
            formatted_results = []
            for doc, score in search_results:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching collection {self.collection_id}: {e}")
            return []
    
    async def list(self, limit: int = 10, offset: int = 0) -> list:
        """List documents in the collection with file information."""
        try:
            from ragbackend.database.files import get_files_by_collection
            
            # Get file metadata for this collection
            files = await get_files_by_collection(
                self.collection_id, 
                self.user_id, 
                limit=limit, 
                offset=offset
            )
            
            # Format for API response
            formatted_files = []
            for file_record in files:
                formatted_file = {
                    "id": file_record['file_id'],
                    "collection_id": self.collection_id,
                    "content": f"File: {file_record['filename']} ({file_record['file_size']} bytes)",
                    "metadata": {
                        "filename": file_record['filename'],
                        "content_type": file_record['content_type'],
                        "file_size": file_record['file_size'],
                        "upload_time": file_record['upload_time'].isoformat() if file_record['upload_time'] else None,
                        "object_path": file_record['object_path']
                    },
                    "created_at": file_record['created_at'].isoformat() if file_record['created_at'] else None,
                    "updated_at": file_record['updated_at'].isoformat() if file_record['updated_at'] else None
                }
                formatted_files.append(formatted_file)
            
            return formatted_files
            
        except Exception as e:
            logger.error(f"Error listing documents in collection {self.collection_id}: {e}")
            return []


class CollectionManager:
    """Manages multiple collections in a database."""

    def __init__(self, user_id: Optional[str] = None):
        """Initialize CollectionManager."""
        self.user_id = user_id

    async def setup(self):
        """Create the collection metadata table if it doesn't exist."""
        async with get_db_connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    uuid UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    table_id TEXT NOT NULL UNIQUE,
                    metadata JSONB,
                    embedding_model TEXT NOT NULL,
                    embedding_dimensions INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    async def create_collection(
        self,
        name: str,
        metadata: Optional[dict[str, Any]] = None,
        embedding_model: str = "default",
        embedding_dimensions: Optional[int] = None,
    ) -> CollectionDetails:
        """Create a new collection."""
        collection_uuid = str(uuid.uuid4())
        table_id = f"collection_{collection_uuid.replace('-', '_')}"

        details: CollectionDetails = {
            "name": name,
            "uuid": collection_uuid,
            "table_id": table_id,
            "metadata": metadata or {},
            "embedding_model": embedding_model,
        }

        if embedding_dimensions:
            details["embedding_dimensions"] = embedding_dimensions

        # Create vectorstore table
        store = await get_vectorstore(collection_name=table_id)

        # Insert collection metadata
        async with get_db_connection() as conn:
            await conn.execute(
                """
                INSERT INTO collections (uuid, name, table_id, metadata, embedding_model, embedding_dimensions)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                collection_uuid,
                name,
                table_id,
                json.dumps(metadata or {}),
                embedding_model,
                embedding_dimensions,
            )

        return details

    async def get_collection(self, collection_uuid: str) -> Collection:
        """Get a collection by UUID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                "SELECT uuid, name, table_id, metadata, embedding_model, embedding_dimensions FROM collections WHERE uuid = $1",
                collection_uuid,
            )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_uuid} not found",
            )

        details: CollectionDetails = {
            "uuid": str(row["uuid"]),
            "name": row["name"],
            "table_id": row["table_id"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "embedding_model": row["embedding_model"],
        }

        if row["embedding_dimensions"]:
            details["embedding_dimensions"] = row["embedding_dimensions"]

        return Collection(
            collection_id=collection_uuid,
            user_id=self.user_id or "",
            details=details
        )

    async def list_collections(self) -> list[CollectionDetails]:
        """List all collections."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                "SELECT uuid, name, table_id, metadata, embedding_model, embedding_dimensions FROM collections ORDER BY name"
            )

        collections = []
        for row in rows:
            details: CollectionDetails = {
                "uuid": str(row["uuid"]),
                "name": row["name"],
                "table_id": row["table_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "embedding_model": row["embedding_model"],
            }

            if row["embedding_dimensions"]:
                details["embedding_dimensions"] = row["embedding_dimensions"]

            collections.append(details)

        return collections

    async def update_collection(
        self,
        collection_uuid: str,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> CollectionDetails:
        """Update collection metadata."""
        async with get_db_connection() as conn:
            # Check if collection exists
            existing = await conn.fetchrow("SELECT * FROM collections WHERE uuid = $1", collection_uuid)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {collection_uuid} not found",
                )

            # Update fields
            updates = []
            values = []
            counter = 1

            if name is not None:
                updates.append(f"name = ${counter}")
                values.append(name)
                counter += 1

            if metadata is not None:
                updates.append(f"metadata = ${counter}")
                values.append(json.dumps(metadata))
                counter += 1

            if updates:
                values.append(collection_uuid)
                query = f"UPDATE collections SET {', '.join(updates)} WHERE uuid = ${counter}"
                await conn.execute(query, *values)

            # Return updated details
            row = await conn.fetchrow(
                "SELECT uuid, name, table_id, metadata, embedding_model, embedding_dimensions FROM collections WHERE uuid = $1",
                collection_uuid,
            )

        details: CollectionDetails = {
            "uuid": str(row["uuid"]),
            "name": row["name"],
            "table_id": row["table_id"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "embedding_model": row["embedding_model"],
        }

        if row["embedding_dimensions"]:
            details["embedding_dimensions"] = row["embedding_dimensions"]

        return details

    async def delete_collection(self, collection_uuid: str, user_id: str) -> bool:
        """Delete a collection and its associated data, including MinIO files."""
        async with get_db_connection() as conn:
            # Get table_id first
            row = await conn.fetchrow("SELECT table_id FROM collections WHERE uuid = $1", collection_uuid)
            if not row:
                return False

            table_id = row["table_id"]

            # Delete all files from MinIO for this collection
            try:
                from ragbackend.services.minio_service import get_minio_service
                from ragbackend.database.files import delete_files_by_collection
                
                minio_service = get_minio_service()
                
                # Delete files from MinIO using the prefix pattern: user_id/collection_id/
                minio_prefix = f"{user_id}/{collection_uuid}/"
                deleted_files = await minio_service.delete_files_by_prefix(minio_prefix)
                logger.info(f"Deleted {deleted_files} files from MinIO for collection {collection_uuid}")
                
                # Delete file metadata from database
                deleted_metadata = await delete_files_by_collection(collection_uuid, user_id)
                logger.info(f"Deleted {deleted_metadata} file metadata records for collection {collection_uuid}")
                
            except Exception as e:
                logger.error(f"Failed to delete MinIO files for collection {collection_uuid}: {e}")
                # Continue with collection deletion even if MinIO cleanup fails

            # Drop the vectorstore table
            try:
                await conn.execute(f"DROP TABLE IF EXISTS vectorstore_{table_id}")
            except Exception as e:
                logger.warning(f"Could not drop table vectorstore_{table_id}: {e}")

            # Delete from collections metadata
            result = await conn.execute("DELETE FROM collections WHERE uuid = $1", collection_uuid)
            
            # Check if any rows were affected
            return result != "DELETE 0"
    
    async def delete(self, collection_uuid: str) -> bool:
        """Delete a collection with user context (wrapper method for API compatibility)."""
        if not self.user_id:
            logger.warning("Attempting to delete collection without user context")
            # Fallback to old behavior without MinIO cleanup
            return await self.delete_collection(collection_uuid, "unknown")
        return await self.delete_collection(collection_uuid, self.user_id)
