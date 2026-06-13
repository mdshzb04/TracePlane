import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.email_policy import validate_allowed_email_domain


class UserRegister(BaseModel):
    """Public registration — role is always assigned server-side."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, value: str) -> str:
        return validate_allowed_email_domain(value)


class UserCreate(BaseModel):
    """Admin-only user creation with explicit role."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None
    role: str = Field(default="viewer", pattern=r"^(admin|developer|viewer)$")

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, value: str) -> str:
        return validate_allowed_email_domain(value)


class UserSelfUpdate(BaseModel):
    """Fields a user may update on their own profile."""

    full_name: Optional[str] = None


class UserAdminUpdate(BaseModel):
    """Admin-only user management fields."""

    full_name: Optional[str] = None
    role: Optional[str] = Field(default=None, pattern=r"^(admin|developer|viewer)$")
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    provider: str = "email"
    github_id: Optional[str] = None
    avatar_url: Optional[str] = None
    has_password: bool = False
    has_github: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SetPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)
    current_password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, value: str) -> str:
        return validate_allowed_email_domain(value)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str | None = None
