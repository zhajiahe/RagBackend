from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentCreate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None


class DocumentUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None


class DocumentResponse(BaseModel):
    id: str
    collection_id: str
    content: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10
    filter: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    id: str
    collection_id: str
    content: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    similarity: float
    created_at: Optional[str] = None
