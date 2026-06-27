# 🚨 RUNBOOK — On-Call Troubleshooting Guide

Quick reference for debugging issues.

> **Note:** For Redis commands, first load your env: `source .env`

---

## 🔍 First Steps (Always)

```bash
# Check what's running and health status
docker compose ps

# Check application health (shows DB + Redis status)
curl http://localhost:8000/health

# View recent logs from all services
docker compose logs --tail 50
```

---

## ❌ Problem: API not responding

**Symptoms:** `curl http://localhost:8000/health` → connection refused

**Steps:**
```bash
# 1. Check logs for crash reason
docker compose logs api --tail 30

# 2. Restart
docker compose restart api

# 3. If still failing — rebuild
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
# 1. Check logs
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
# 1. Check logs
docker compose logs redis --tail 20

# 2. Check memory usage
docker compose exec redis redis-cli -a $REDIS_PASSWORD info memory

# 3. Restart Redis
docker compose restart redis
```

**Common causes:**
- Memory limit reached (should auto-evict with LRU, but check)
- Container crashed
- Password mismatch (`REDIS_PASSWORD` in `.env` doesn't match what Redis was started with)

**Note:** Redis is only a cache. If it's down, the API still works (just slower — reads from DB directly). Rate limiting will also be disabled temporarily.

---

## ❌ Problem: "Internal Server Error" on POST /shorten

**Steps:**
```bash
# 1. Check API logs for the actual error
docker compose logs api --tail 30 | grep -i error

# 2. Common fix: DB schema mismatch — reset the database
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
docker compose exec redis redis-cli -a $REDIS_PASSWORD GET "url:YOUR_CODE"
```

---

## ❌ Problem: User getting 429 (rate limited)

**Steps:**
```bash
# Check if IP is blocked
docker compose exec redis redis-cli -a $REDIS_PASSWORD GET "blocked:THEIR_IP"

# Unblock manually
docker compose exec redis redis-cli -a $REDIS_PASSWORD DEL "blocked:THEIR_IP"
```

---

## 📊 Monitoring Commands

```bash
# Live resource usage
docker stats

# Count URLs in database
docker compose exec db psql -U postgres -d urlshortener \
  -c "SELECT count(*) FROM urls"

# Check Redis memory
docker compose exec redis redis-cli -a $REDIS_PASSWORD info memory | grep used_memory_human

# Full restart (keep data)
docker compose down && docker compose up -d

# Full restart (fresh start, DELETES DATA)
docker compose down -v && docker compose up --build -d
```

---

## 🔑 Key Info

| Service | Port | Container Name |
|---------|------|----------------|
| API | 8000 (exposed to host) | url-shortener-api |
| PostgreSQL | 5432 (internal only) | url-shortener-db |
| Redis | 6379 (internal only) | url-shortener-redis |

> DB and Redis are not exposed to the host. Use `docker compose exec` to access them.

| Log Level | When |
|-----------|------|
| `info` | Normal operations (url_created, cache_hit) |
| `warning` | Degraded state (redis_get_failed, health_check_degraded, ip_blocked) |
| `error` | Something broke (short_code_collision_exhausted) |
