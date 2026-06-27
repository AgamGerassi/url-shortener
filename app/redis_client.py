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


async def check_rate_limit(ip: str, limit: int = None, prefix: str = "rate") -> bool:
    """Check if IP has exceeded rate limit. Returns True if allowed, False if blocked."""
    if limit is None:
        limit = settings.RATE_LIMIT_POST_PER_MINUTE
    try:
        if await redis_client.get(f"blocked:{ip}"):
            return False

        key = f"{prefix}:{ip}"
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, 60)  # 1 minute window

        if current > limit:
            await redis_client.set(f"blocked:{ip}", "1", ex=3600)  # Block IP for 1 hour
            logger.warning("ip_blocked", ip=ip, requests=current, type=prefix)
            return False

        return True
    except Exception as e:
        logger.warning("rate_limit_check_failed", ip=ip, error=str(e))
        return True  # If Redis is down, allow the request
