# 🚨 RUNBOOK — On-Call Troubleshooting Guide

Quick reference for debugging issues.

---

## 🔍 First Steps (Always)

```bash
# Check what's running
docker compose ps

# Check health
curl http://localhost:8000/health

# View recent logs
docker compose logs --tail 50

# View specific service logs
docker compose logs api --tail 30
docker compose logs db --tail 30
docker compose logs redis --tail 30
```

---

## ❌ Problem: API not responding

**Symptoms:** `curl http://localhost:8000/health` → connection refused

**Steps:**
```bash
# 1. Is the container running?
docker compose ps api

# 2. Check logs for crash reason
docker compose logs api --tail 50

# 3. Restart
docker compose restart api

# 4. If still failing — rebuild
docker compose up --build api -d
```

**Common causes:**
- Out of memory (check `docker stats`)
- Failed 5 times → stopped (restart policy: `on-failure:5`)
- DB not ready when API started → restart API

---

## ❌ Problem: Database unhealthy

**Symptoms:** `/health` returns `{"database": "unhealthy"}`

**Steps:**
```bash
# 1. Check DB container
docker compose ps db
docker compose logs db --tail 30

# 2. Can you connect manually?
docker compose exec db psql -U postgres -d urlshortener -c "SELECT 1"

# 3. Check disk space (DB volume full?)
docker system df

# 4. Restart DB
docker compose restart db

# 5. Nuclear option — reset DB (DELETES ALL DATA)
docker compose down -v
docker compose up --build -d
```

**Common causes:**
- Disk full
- Too many connections
- Password mismatch (changed `.env` without resetting volume)

---

## ❌ Problem: Redis unhealthy

**Symptoms:** `/health` returns `{"redis": "unhealthy"}`

**Steps:**
```bash
# 1. Check Redis container
docker compose ps redis
docker compose logs redis --tail 20

# 2. Can you ping it?
docker compose exec redis redis-cli ping

# 3. Check memory usage
docker compose exec redis redis-cli info memory

# 4. Restart Redis
docker compose restart redis
```

**Common causes:**
- Memory limit reached (should auto-evict with LRU, but check)
- Container crashed

**Note:** Redis is only a cache. If it's down, the API still works (just slower — reads from DB directly).

---

## ❌ Problem: "Internal Server Error" on POST /shorten

**Steps:**
```bash
# 1. Check API logs for the actual error
docker compose logs api --tail 30 | grep -i error

# 2. Common: DB schema mismatch
# Fix: reset the database
docker compose down -v
docker compose up --build -d
```

**Common causes:**
- DB schema changed but old volume still exists → reset with `-v`
- DB connection pool exhausted

---

## ❌ Problem: Redirects not working (404 on valid short code)

**Steps:**
```bash
# 1. Check if the code exists in DB
docker compose exec db psql -U postgres -d urlshortener \
  -c "SELECT * FROM urls WHERE short_code = 'YOUR_CODE'"

# 2. Check Redis cache
docker compose exec redis redis-cli GET "url:YOUR_CODE"
```

---

## 📊 Monitoring Commands

```bash
# Live resource usage
docker stats

# Check container health status
docker compose ps

# Count URLs in database
docker compose exec db psql -U postgres -d urlshortener \
  -c "SELECT count(*) FROM urls"

# Check Redis memory
docker compose exec redis redis-cli info memory | grep used_memory_human

# Full restart (keep data)
docker compose down && docker compose up -d

# Full restart (fresh start, DELETES DATA)
docker compose down -v && docker compose up --build -d
```

---

## 🔑 Key Info

| Service | Port | Container Name |
|---------|------|----------------|
| API | 8000 | url-shortener-api |
| PostgreSQL | 5432 | url-shortener-db |
| Redis | 6379 | url-shortener-redis |

| Log Level | When |
|-----------|------|
| `info` | Normal operations (url_created, cache_hit) |
| `warning` | Degraded state (redis_get_failed, health_check_degraded) |
| `error` | Something broke (short_code_collision_exhausted) |
