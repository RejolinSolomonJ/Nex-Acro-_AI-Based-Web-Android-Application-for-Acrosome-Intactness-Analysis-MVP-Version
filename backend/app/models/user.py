"""
User document model for MongoDB (Beanie ODM).
"""

from datetime import datetime
from typing import Optional

from beanie import Document
from pydantic import EmailStr, Field


class User(Document):
    """User account for admin dashboard access."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    role: str = Field(default="user")  # "admin" | "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = ["email", "username"]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@acrosome.ai",
                "full_name": "System Admin",
                "role": "admin",
            }
        }
