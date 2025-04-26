from typing import List, Optional
import logging
from fastapi import UploadFile

from langchain_core.documents.base import Blob, Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.parsers import BS4HTMLParser, PDFMinerParser
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.msword import MsWordParser
from langchain_community.document_loaders.parsers.txt import TextParser

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
    file: UploadFile, metadata: Optional[dict] = None
) -> List[Document]:
    """Process an uploaded file into LangChain documents."""
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

    # If a single parsed doc was split into multiple, update the name metadata
    # Check if the original parse resulted in a single doc and it was split
    if len(docs) == 1 and len(split_docs) > 1:
        original_name = (
            docs[0].metadata.get("name")
            if hasattr(docs[0], "metadata") and isinstance(docs[0].metadata, dict)
            else None
        )
        if original_name:
            for i, split_doc in enumerate(split_docs):
                # Ensure metadata attribute exists and is a dict before updating
                if not hasattr(split_doc, "metadata") or not isinstance(
                    split_doc.metadata, dict
                ):
                    split_doc.metadata = {}  # Initialize if it doesn't exist
                split_doc.metadata["name"] = f"{i + 1}-{original_name}"

    return split_docs


async def index_document(collection_name: str, document_data: dict):
    """Index a document into the vector store."""
    # In a real implementation, this would index into PGVector
    LOGGER.info(f"Indexing document into collection {collection_name}: {document_data}")
