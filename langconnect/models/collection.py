from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID
import datetime

# =====================
# Collection Schemas
# =====================


class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    # user_id will be handled separately, often from auth context


class CollectionCreate(CollectionBase):
    pass  # Inherits name, description


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CollectionResponse(CollectionBase):
    id: UUID
    user_id: UUID  # Added user_id
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True  # For SQLAlchemy or similar ORMs if used later
        from_attributes = True  # Pydantic v2 way


# =====================
# Document Schemas
# =====================


class DocumentBase(BaseModel):
    page_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # collection_id is needed but often passed separately or inferred
    # embedding might be generated later


class DocumentCreate(DocumentBase):
    collection_id: UUID
    embedding: Optional[List[float]] = (
        None  # Embedding can be added during creation or later
    )


class DocumentUpdate(BaseModel):
    page_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class DocumentResponse(DocumentBase):
    id: UUID
    collection_id: UUID
    embedding: Optional[List[float]] = None  # Represent embedding as list of floats
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True
        from_attributes = True  # Pydantic v2 way


# Example of how you might represent embedding if using pgvector directly
# class DocumentResponse(DocumentBase):
#     id: UUID
#     collection_id: UUID
#     embedding: Optional[str] = None # Store as string representation from pgvector if needed
#     created_at: datetime.datetime
#     updated_at: datetime.datetime
#
#     class Config:
#         orm_mode = True
