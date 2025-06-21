import datetime
from typing import Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# =====================
# Collection Schemas
# =====================


class CollectionCreate(BaseModel):
    """Schema for creating a new collection."""

    name: str = Field(..., description="The unique name of the collection.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional metadata for the collection."
    )


class CollectionUpdate(BaseModel):
    """Schema for updating an existing collection."""

    name: str | None = Field(None, description="New name for the collection.")
    metadata: dict[str, Any] | None = Field(
        None, description="Updated metadata for the collection."
    )


class CollectionResponse(BaseModel):
    """Schema for representing a collection from PGVector."""

    # PGVector table has uuid (id), name (str), and cmetadata (JSONB)
    # We get these from list/get db functions
    uuid: Union[str, UUID] = Field(
        ..., description="The unique identifier of the collection in PGVector."
    )
    name: str = Field(..., description="The name of the collection.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata associated with the collection."
    )

    @field_validator('uuid')
    @classmethod
    def validate_uuid(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        # Allows creating model from dict like
        # {'uuid': '...', 'name': '...', 'metadata': {...}}
        from_attributes = True


# =====================
# Document Schemas
# =====================


class DocumentBase(BaseModel):
    page_content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    collection_id: Union[str, UUID]
    embedding: list[float] | None = (
        None  # Embedding can be added during creation or later
    )

    @field_validator('collection_id')
    @classmethod
    def validate_collection_id(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, UUID):
            return str(v)
        return v


class DocumentUpdate(BaseModel):
    page_content: str | None = None
    metadata: dict[str, Any] | None = None
    embedding: list[float] | None = None


class DocumentResponse(DocumentBase):
    id: Union[str, UUID]
    collection_id: Union[str, UUID]
    embedding: list[float] | None = None  # Represent embedding as list of floats
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator('id', 'collection_id')
    @classmethod
    def validate_uuid_fields(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True  # Pydantic v2 way
