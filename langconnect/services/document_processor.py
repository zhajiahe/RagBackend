from typing import List
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


async def process_document(file: UploadFile) -> List[Document]:
    """Process an uploaded file into LangChain documents."""
    contents = await file.read()
    blob = Blob(data=contents, mimetype=file.content_type or "text/plain")

    docs = MIMETYPE_BASED_PARSER.parse(blob)
    # Split documents
    split_docs = TEXT_SPLITTER.split_documents(docs)
    return split_docs


async def index_document(collection_id: str, document_data: dict):
    """Index a document into the vector store."""
    # In a real implementation, this would index into PGVector
    LOGGER.info(f"Indexing document into collection {collection_id}: {document_data}")
