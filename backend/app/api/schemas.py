import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

TELEGRAM_RE = re.compile(r"^@[A-Za-z0-9_]{5,32}$")


class LoginRequest(BaseModel):
    email: EmailStr
    otp: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=6,
    )


class LoginResponse(BaseModel):
    message: str
    expires_at: Optional[datetime] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None


class ProfileResponse(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    about: Optional[str] = None
    telegram: Optional[str] = None
    interests: List[str]
    is_active: bool


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    about: Optional[str] = Field(default=None, max_length=500)
    telegram: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=32,
    )
    interests: Optional[List[str]] = None

    @field_validator("telegram")
    @classmethod
    def validate_telegram(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not TELEGRAM_RE.match(value):
            raise ValueError(
                "Telegram alias must start with @ and be 5-32 chars",
            )
        return value

    @field_validator("interests")
    @classmethod
    def validate_interests(
        cls,
        value: Optional[List[str]],
    ) -> Optional[List[str]]:
        if value is None:
            return value
        if len(value) > 20:
            raise ValueError("Too many interests (max 20)")
        cleaned: List[str] = []
        for item in value:
            if not item or not item.strip():
                raise ValueError("Interest cannot be empty")
            if len(item.strip()) > 50:
                raise ValueError("Interest too long (max 50)")
            cleaned.append(item)
        return cleaned
