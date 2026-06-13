# My Portfolio App

Short Description: a project for my own portfolio

Languages: flask (python)

## CREATE A VIRTUAL ENVIRONMENT

1. run command: `python -m venv .venv`
2. run command: `.\.venv\Scripts\activate.bat`

## INSTALL PACKAGE

- `cd app && pip install -r requirements.txt` or run `make package-install`

## LANGUAGE TRANSLATION COMMANDS

1. `pybabel extract -F babel.cfg -o messages.pot .`
2. `pybabel init -i messages.pot -d translations -l ceb`
3. `pybabel init -i messages.pot -d translations -l en`
4. `pybabel compile -d translations`

## START UP

1. run command: `make start-build`

## DDoS / Abuse Protection (Render + Cloudflare)

This project now includes an app-level request guard (`app/security/ddos_guard.py`) for:
- per-IP rate limits (global + sensitive endpoints)
- admin login throttling
- comment/like spam throttling
- media proxy/download throttling
- basic security headers

Important:
- App-level limits do **not** stop large network/volumetric DDoS by themselves.
- Use an edge provider (Cloudflare) in front of Render for real DDoS protection.

### Recommended deployment setup

1. Put your domain behind Cloudflare (orange-cloud proxy enabled).
2. Point Cloudflare DNS to your Render service domain.
3. In Cloudflare, enable:
   - `Bot Fight Mode` (or Super Bot Fight Mode if available)
   - `WAF Managed Rules`
   - `Rate Limiting Rules`
   - `Under Attack Mode` (temporarily during active attack)
4. In Render:
   - keep the service private admin URLs unindexed
   - scale instance size/workers if needed
   - monitor logs for repeated 429s / attack patterns

### Cloudflare rate-limit rules (starting point)

- `POST /admin/login`: block/challenge after `5-10 requests / 5 min / IP`
- `POST /api/gallery-comments*`, `POST /api/vlog-comments*`: challenge after `10-20 requests / min / IP`
- `POST /api/gallery-like*`, `POST /api/vlog-like*`: challenge after `20-60 requests / min / IP`
- `GET /api/proxy-audio*`, `GET /api/download_song*`: rate limit aggressively per IP (these are expensive)
- Global fallback: challenge high request rates to `/*` (tune based on normal traffic)

### Multi-worker / multi-instance rate limiting (Redis)

The app supports Redis-backed Flask-Caching via env vars. This is recommended if you use multiple workers/instances so rate limits are shared.

Set these in Render environment variables:

- `CACHE_TYPE=RedisCache`
- `CACHE_REDIS_URL=<your redis url>`
- `CACHE_DEFAULT_TIMEOUT=86400`
- `CACHE_KEY_PREFIX=jpa_profile:`

You can use a managed Redis service (e.g. Upstash/Redis Cloud).

### App-level DDoS guard env vars (optional tuning)

- `DDOS_GUARD_ENABLED=true`
- `MAX_CONTENT_LENGTH_BYTES=314572800`
- `DDOS_GUARD_GLOBAL_BURST_LIMIT=80`
- `DDOS_GUARD_GLOBAL_BURST_WINDOW=10`
- `DDOS_GUARD_GLOBAL_SUSTAINED_LIMIT=900`
- `DDOS_GUARD_GLOBAL_SUSTAINED_WINDOW=300`
- `DDOS_GUARD_MEDIA_BURST_LIMIT=12`
- `DDOS_GUARD_MEDIA_BURST_WINDOW=10`
- `DDOS_GUARD_MEDIA_SUSTAINED_LIMIT=120`
- `DDOS_GUARD_MEDIA_SUSTAINED_WINDOW=300`
- `DDOS_GUARD_ENGAGEMENT_BURST_LIMIT=10`
- `DDOS_GUARD_ENGAGEMENT_BURST_WINDOW=10`
- `DDOS_GUARD_ENGAGEMENT_SUSTAINED_LIMIT=120`
- `DDOS_GUARD_ENGAGEMENT_SUSTAINED_WINDOW=300`
- `DDOS_GUARD_ADMIN_LOGIN_LIMIT=8`
- `DDOS_GUARD_ADMIN_LOGIN_WINDOW=300`
- `DDOS_GUARD_DEVICE_INFO_LIMIT=30`
- `DDOS_GUARD_DEVICE_INFO_WINDOW=60`
