import redis.asyncio as redis
import structlog
from app.config import settings

logger = structlog.get_logger()

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    retry_on_timeout=True,
)


async def get_cached_url(short_code: str) -> str | None:
    """Get a URL from Redis cache."""
    try:
        return await redis_client.get(f"url:{short_code}")
    except Exception as e:
        logger.warning("redis_get_failed", short_code=short_code, error=str(e))
        return None


async def set_cached_url(short_code: str, original_url: str) -> None:
    """Cache a URL in Redis with TTL."""
    try:
        await redis_client.set(
            f"url:{short_code}",
            original_url,
            ex=settings.REDIS_TTL_SECONDS,
        )
    except Exception as e:
        logger.warning("redis_set_failed", short_code=short_code, error=str(e))


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False
