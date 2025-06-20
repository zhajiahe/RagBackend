"""User schemas for authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for user creation."""
    
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    
    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class Token(BaseModel):
    """Token response schema."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data schema."""
    
    username: Optional[str] = None
    user_id: Optional[str] = None 