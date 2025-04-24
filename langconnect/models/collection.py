from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import datetime

# =====================
# Collection Schemas
# =====================


class CollectionCreate(BaseModel):
    """Schema for creating a new collection (only name is needed)."""

    name: str = Field(..., description="The unique name of the collection.")


class CollectionResponse(BaseModel):
    """Schema for representing a collection from PGVector."""

    # PGVector table has uuid (UUID) and name (str)
    # We get these from list/get db functions
    uuid: str = Field(
        ..., description="The unique identifier (UUID) of the collection in PGVector."
    )
    name: str = Field(..., description="The name of the collection.")

    class Config:
        from_attributes = (
            True  # Allows creating model from dict like {'uuid': '...', 'name': '...'}
        )


# =====================
# Document Schemas
# =====================


class DocumentBase(BaseModel):
    page_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # collection_id is needed but often passed separately or inferred
    # embedding might be generated later


class DocumentCreate(DocumentBase):
    collection_id: str
    embedding: Optional[List[float]] = (
        None  # Embedding can be added during creation or later
    )


class DocumentUpdate(BaseModel):
    page_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class DocumentResponse(DocumentBase):
    id: str
    collection_id: str
    embedding: Optional[List[float]] = None  # Represent embedding as list of floats
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True
        from_attributes = True  # Pydantic v2 way
