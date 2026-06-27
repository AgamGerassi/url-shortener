from pydantic import BaseModel, field_validator
from datetime import datetime
import re
from app.config import settings


class URLCreate(BaseModel):
    """Request schema for creating a short URL."""
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if len(v) > settings.MAX_URL_LENGTH:
            raise ValueError(f"URL must be less than {settings.MAX_URL_LENGTH} characters")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        # Validate URL format (must have a valid domain with TLD)
        url_pattern = re.compile(
            r'^https?://'
            r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}' 
            r'(:\d{1,5})?'                      
            r'(/.*)?$'                      
        )
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format")

        return v


class URLResponse(BaseModel):
    """Response schema for a created short URL."""
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime


class URLStats(BaseModel):
    """Response schema for URL statistics."""
    short_code: str
    original_url: str
    created_at: datetime


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    database: str
    redis: str
    version: str
