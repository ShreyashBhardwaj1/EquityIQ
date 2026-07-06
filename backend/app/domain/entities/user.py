"""
User entity representing system credentials and metadata.
"""

import re
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRole(StrEnum):
    """
    Role definitions for Role-Based Access Control (RBAC).
    """

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(BaseModel):
    """
    User domain entity representing account credentials and access privilege levels.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    email: str = Field(description="Unique email address for user login")
    hashed_password: str | None = Field(
        default=None, description="Salted cryptographically hashed password"
    )
    oauth_provider: str | None = Field(
        default=None, description="Optional authentication provider name"
    )
    role: UserRole = Field(
        default=UserRole.VIEWER, description="RBAC access level role"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record update timestamp"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """
        Validates the structure of the email address string.
        """
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address format.")
        return v.lower().strip()
