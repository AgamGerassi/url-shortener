from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/urlshortener"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_TTL_SECONDS: int = 3600  # Cache TTL: 1 hour

    # Application
    BASE_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "production"
    SHORT_CODE_LENGTH: int = 7
    MAX_URL_LENGTH: int = 2048

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
