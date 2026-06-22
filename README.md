# URL Shortener

A production-ready URL shortener service built with FastAPI, PostgreSQL, and Redis.

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd url-shortener

# 2. Copy environment variables
cp .env.example .env

# 3. Run everything
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/shorten` | Create a short URL |
| `GET` | `/{code}` | Redirect to original URL |
| `GET` | `/{code}/stats` | Get access statistics |
| `GET` | `/health` | Health check (DB + Redis) |

### Examples

**Create a short URL:**
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/very/long/path"}'
```

**Response:**
```json
{
  "short_code": "aB3dEfG",
  "short_url": "http://localhost:8000/aB3dEfG",
  "original_url": "https://www.example.com/very/long/path",
  "created_at": "2024-01-15T10:30:00"
}
```

**Follow a short URL:**
```bash
curl -L http://localhost:8000/aB3dEfG
```

## Architecture

```
┌──────────┐     ┌───────────┐     ┌────────────┐
│  Client  │────▶│  FastAPI   │────▶│ PostgreSQL │
└──────────┘     │   (API)    │     └────────────┘
                 │            │────▶┌────────────┐
                 └───────────┘     │   Redis    │
                                    └────────────┘
```

- **FastAPI** - Handles HTTP requests, URL creation, and redirects
- **PostgreSQL** - Persistent storage for URL mappings
- **Redis** - LRU cache for fast lookups, reduces DB load

## Design Decisions

### Why FastAPI?
- Async by default (great for I/O-bound work like DB/Redis calls)
- Built-in request validation via Pydantic
- Auto-generated API documentation
- Widely adopted, easy for the next engineer to pick up

### Multi-stage Docker Build
- **Builder stage**: installs dependencies
- **Production stage**: only copies the virtualenv and app code
- Result: smaller image (~150MB vs ~900MB full Python image)

### Security Hardening
- Container runs as non-root user (`appuser`)
- Read-only filesystem in production
- Resource limits (CPU/memory) to prevent noisy-neighbor issues
- No debug endpoints in production mode
- URL validation to prevent injection

### Data Persistence
- PostgreSQL data stored in a named Docker volume (`postgres_data`)
- Survives `docker compose down` and container restarts
- To fully reset: `docker compose down -v`

### Caching Strategy
- Redis with LRU eviction policy (`allkeys-lru`)
- 1-hour TTL on cached entries
- Graceful degradation: if Redis is down, app still works via DB

### Health Checks
- Docker-level HEALTHCHECK in Dockerfile
- Compose-level health checks for dependency ordering
- Application-level `/health` endpoint checks both DB and Redis

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | postgres | Database user |
| `POSTGRES_PASSWORD` | postgres | Database password |
| `POSTGRES_DB` | urlshortener | Database name |
| `BASE_URL` | http://localhost:8000 | Public URL for generated links |
| `ENVIRONMENT` | production | `production` or `development` |
| `REDIS_TTL_SECONDS` | 3600 | Cache TTL |

## Stopping

```bash
# Stop containers (keep data)
docker compose down

# Stop and delete all data
docker compose down -v
```
