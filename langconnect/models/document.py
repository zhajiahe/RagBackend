from typing import Dict, Optional, Any
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    id: str
    collection_id: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
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
    metadata: Optional[Dict[str, Any]] = None
    similarity: float
    created_at: Optional[str] = None
