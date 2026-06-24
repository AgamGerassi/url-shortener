# 🔗 URL Shortener

A URL shortener service built with **FastAPI**, **PostgreSQL**, and **Redis**.

## 🚀 Quick Start

```bash
git clone https://github.com/AgamGerassi/url-shortener.git && cd url-shortener

# Set up your environment variables:
cp .env.example .env
nano .env  # Edit values as needed (database password, ports, etc.)

# Run the app:
chmod +x start.sh
./start.sh
```

The script will automatically:
1. Verify that all required dependencies are installed (and install any that are missing)
2. Build and start all services
3. Wait for health checks and confirm everything is running

The API will be available at `http://localhost:8000`.

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/shorten` | Create a short URL |
| `GET` | `/{code}` | Redirect to original URL |
| `GET` | `/{code}/stats` | Get access statistics |
| `GET` | `/health` | Health check (DB + Redis) |
| `GET` | `/docs` | Interactive API documentation (development only) |

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

## 🏗️ Architecture

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

## ⚙️ Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | postgres | Database user |
| `POSTGRES_PASSWORD` | postgres | Database password |
| `POSTGRES_DB` | urlshortener | Database name |
| `BASE_URL` | http://localhost:8000 | Public URL for generated links |
| `ENVIRONMENT` | production | `production` or `development` |
| `REDIS_TTL_SECONDS` | 3600 | Cache TTL (seconds) |
| `WORKERS` | 2 | Number of uvicorn workers |
| `API_PORT` | 8000 | Host port for the API |

## Stopping

```bash
# Stop containers (keep data)
docker compose down

# Stop and delete all data
docker compose down -v
```

## 🚨 Troubleshooting

See [RUNBOOK.md](RUNBOOK.md) for on-call debugging guide.
