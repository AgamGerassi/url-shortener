import secrets
import string
import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import URL
from app.schemas import URLCreate, URLResponse, URLStats, HealthResponse
from app.redis_client import get_cached_url, set_cached_url, check_redis_health
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()


def generate_short_code(length: int = settings.SHORT_CODE_LENGTH) -> str:
    """Generate a random short code using URL-safe characters."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("/health", response_model=HealthResponse, tags=["monitoring"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint for monitoring and container orchestration."""
    # Check database
    db_status = "healthy"
    try:
        await db.execute(select(1))
    except Exception:
        db_status = "unhealthy"

    # Check Redis
    redis_status = "healthy" if await check_redis_health() else "unhealthy"

    overall = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    if overall != "healthy":
        logger.warning("health_check_degraded", database=db_status, redis=redis_status)

    return HealthResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
        version="1.0.0",
    )


@router.post("/shorten", response_model=URLResponse, status_code=201, tags=["urls"])
async def create_short_url(payload: URLCreate, db: AsyncSession = Depends(get_db)):
    """Create a shortened URL."""
    # Generate a unique short code (retry if collision)
    for _ in range(10):
        short_code = generate_short_code()
        existing = await db.execute(select(URL).where(URL.short_code == short_code))
        if not existing.scalar_one_or_none():
            break
    else:
        logger.error("short_code_collision_exhausted", url=payload.url)
        raise HTTPException(status_code=500, detail="Could not generate unique code")

    # Save to database
    url_entry = URL(short_code=short_code, original_url=payload.url)
    db.add(url_entry)
    await db.flush()
    await db.refresh(url_entry)

    # Cache in Redis
    await set_cached_url(short_code, payload.url)

    logger.info("url_created", short_code=short_code, original_url=payload.url)

    return URLResponse(
        short_code=short_code,
        short_url=f"{settings.BASE_URL}/{short_code}",
        original_url=payload.url,
        created_at=url_entry.created_at,
    )


@router.get("/{short_code}", tags=["urls"])
async def redirect_to_url(short_code: str, db: AsyncSession = Depends(get_db)):
    """Redirect a short code to its original URL."""
    # Try cache first
    cached_url = await get_cached_url(short_code)
    if cached_url:
        logger.info("cache_hit", short_code=short_code)
        # Update access count in background (fire and forget is fine here)
        result = await db.execute(select(URL).where(URL.short_code == short_code))
        url_entry = result.scalar_one_or_none()
        if url_entry:
            url_entry.access_count += 1
        return RedirectResponse(url=cached_url, status_code=307)

    # Cache miss - query database
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_entry = result.scalar_one_or_none()

    if not url_entry:
        logger.info("url_not_found", short_code=short_code)
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Update cache and access count
    await set_cached_url(short_code, url_entry.original_url)
    url_entry.access_count += 1

    logger.info("cache_miss_resolved", short_code=short_code)
    return RedirectResponse(url=url_entry.original_url, status_code=307)


@router.get("/{short_code}/stats", response_model=URLStats, tags=["urls"])
async def get_url_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    """Get statistics for a shortened URL."""
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_entry = result.scalar_one_or_none()

    if not url_entry:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return URLStats(
        short_code=url_entry.short_code,
        original_url=url_entry.original_url,
        created_at=url_entry.created_at,
        access_count=url_entry.access_count,
    )
