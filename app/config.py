from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db:5432/urlshortener"

    REDIS_URL: str = "redis://:password@redis:6379/0"
    REDIS_TTL_SECONDS: int = 3600  # 1 hour

    BASE_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "production"
    SHORT_CODE_LENGTH: int = 7
    MAX_URL_LENGTH: int = 2048
    RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
