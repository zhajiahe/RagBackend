import logging
import uuid
from typing import Optional, Dict, Any, Tuple

from fastapi import UploadFile
from langchain_community.document_loaders.parsers import BS4HTMLParser, PDFMinerParser
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.msword import MsWordParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_core.documents.base import Blob, Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ragbackend.services.minio_service import get_minio_service
from ragbackend.database.files import insert_file_metadata

LOGGER = logging.getLogger(__name__)

# Document Parser Configuration
HANDLERS = {
    "application/pdf": PDFMinerParser(),
    "text/plain": TextParser(),
    "text/html": BS4HTMLParser(),
    "application/msword": MsWordParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        MsWordParser()
    ),
}

SUPPORTED_MIMETYPES = sorted(HANDLERS.keys())

MIMETYPE_BASED_PARSER = MimeTypeBasedParser(
    handlers=HANDLERS,
    fallback_parser=None,
)

# Text Splitter
TEXT_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


async def process_document(
    file: UploadFile, 
    metadata: dict | None = None,
    user_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    store_original: bool = True
) -> Tuple[list[Document], Optional[Dict[str, Any]]]:
    """
    Process an uploaded file into LangChain documents and optionally store original in MinIO.
    
    Args:
        file: The uploaded file
        metadata: Additional metadata to add to documents
        user_id: User ID for MinIO storage (required if store_original=True)
        collection_id: Collection ID for MinIO storage (required if store_original=True)
        store_original: Whether to store the original file in MinIO
        
    Returns:
        Tuple of (processed documents, file metadata from MinIO storage)
    """
    # Generate a unique ID for this file processing instance
    file_id = str(uuid.uuid4())
    
    # Store original file in MinIO if requested
    file_metadata = None
    if store_original and user_id and collection_id:
        try:
            minio_service = get_minio_service()
            file_metadata = await minio_service.upload_file(
                file, user_id, collection_id, file_id
            )
            
            # Store file metadata in database
            if file_metadata:
                db_file_id = await insert_file_metadata(file_metadata)
                if db_file_id:
                    file_metadata['db_id'] = db_file_id
                    LOGGER.info(f"File stored in MinIO and metadata saved to DB: {file.filename}")
                else:
                    LOGGER.warning(f"File stored in MinIO but failed to save metadata to DB: {file.filename}")
            
        except Exception as e:
            LOGGER.error(f"Failed to store original file in MinIO: {e}")
            # Continue with processing even if MinIO storage fails
    
    # Read file contents for processing
    contents = await file.read()
    blob = Blob(data=contents, mimetype=file.content_type or "text/plain")

    docs = MIMETYPE_BASED_PARSER.parse(blob)

    # Add provided metadata to each document
    if metadata:
        for doc in docs:
            # Ensure metadata attribute exists and is a dict
            if not hasattr(doc, "metadata") or not isinstance(doc.metadata, dict):
                doc.metadata = {}
            # Update with provided metadata, preserving existing keys if not overridden
            doc.metadata.update(metadata)

    # Split documents
    split_docs = TEXT_SPLITTER.split_documents(docs)

    # Add the generated file_id and MinIO info to all split documents' metadata
    for split_doc in split_docs:
        if not hasattr(split_doc, "metadata") or not isinstance(
            split_doc.metadata, dict
        ):
            split_doc.metadata = {}  # Initialize if it doesn't exist
        
        split_doc.metadata["file_id"] = file_id  # Store as string for compatibility
        
        # Add MinIO file information if available
        if file_metadata:
            split_doc.metadata["original_file"] = {
                "object_path": file_metadata.get("object_path"),
                "filename": file_metadata.get("filename"),
                "size": file_metadata.get("size"),
                "content_type": file_metadata.get("content_type"),
                "upload_time": file_metadata.get("upload_time")
            }

    return split_docs, file_metadata


# Backwards compatibility: keep the original function signature
async def process_document_legacy(
    file: UploadFile, metadata: dict | None = None
) -> list[Document]:
    """Legacy version of process_document for backwards compatibility."""
    split_docs, _ = await process_document(
        file=file,
        metadata=metadata,
        store_original=False
    )
    return split_docs
