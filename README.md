# My Portfolio App

Short Description: a project for my own portfolio

Languages: flask (python)

## PREREQUISITES

- Python **3.11** (the app is tested on Python 3.11; newer versions may require dependency updates)

## CREATE A VIRTUAL ENVIRONMENT

> **Note:** Run the following commands in Windows Command Prompt (cmd).

1. run command: `py -3.11 -m venv .venv`
2. run command: `.\.venv\Scripts\activate.bat`

## INSTALL PACKAGE

- `cd app && py -3.11 -m pip install -r requirements.txt` or run `make package-install`

## LANGUAGE TRANSLATION COMMANDS

1. `pybabel extract -F babel.cfg -o messages.pot .`
2. `pybabel init -i messages.pot -d translations -l ceb`
3. `pybabel init -i messages.pot -d translations -l en`
4. `pybabel compile -d translations`

## START UP

1. run command: `npm install` in the project root directory
2. run command: `make start-build`

## DOCKER

Prerequisites: Docker Desktop installed and running.

1. Create the env file (the container reads it at runtime):

   - copy `app/.env.example` to `app/.env` and fill in real values (`MONGO_URI`, `SECRET_KEY`, ...)

   The image already bakes the frontend (`npm run build:frontend`, `FRONTEND_DIST=1`), so no local Node build is needed to run it.

### Option A: Docker Compose (recommended)

- run command: `docker compose up --build` in the project root directory
- open `http://localhost:5000`
- stop: `docker compose down`

Compose builds the root `Dockerfile`, loads `./app/.env` when present, and sets `PORT=5000` (the image starts `gunicorn --bind :$PORT`, so the published port always matches the in-container port).

### Live development (see local edits instantly, no rebuild)

`compose.dev.yaml` bind-mounts your local `./app` into the container, runs the Flask dev server (auto-reloads on `.py` changes), serves source templates instead of the built `dist` output, disables the server page cache (`CACHE_TYPE=null`), and turns on template live-reload in the browser:

```bash
make run-docker-local
```

Build once — after that, editing any file under `app/` (Python, templates, static) shows up on refresh with no rebuild and no `docker` cache to clear. Stop with:

```bash
make stop-docker-local
```

Notes:

- Python changes trigger an automatic server restart (a few seconds); template/static changes apply on the next browser refresh.
- If the browser still shows an old page, it is the *browser* cache, not Docker: hard-refresh (`Ctrl+Shift+R`) or test with `curl`.
- For frontend Vite hot-reload (`:5173` + `VITE_DEV_SERVER`), keep using `npm run dev` outside Docker.

### Local custom domains (`*.jpastack.local`)

The app separates traffic by hostname (`app/domains.py`):

- Professional landing: `http://professional.jpastack.local`
- Social landing: `http://jpastack.local` or `http://social.jpastack.local`
- Admin/config (incl. admin login): `http://config.jpastack.local`

Two one-time setup steps are required before those URLs resolve:

1. Map the names to localhost. Run Notepad **as Administrator**, open `C:\Windows\System32\drivers\etc\hosts`, and add:

   ```
   127.0.0.1 jpastack.local
   127.0.0.1 professional.jpastack.local
   127.0.0.1 social.jpastack.local
   127.0.0.1 config.jpastack.local
   ```

2. Recreate the container so the port mapping applies: `docker compose up -d --build`.

Compose publishes both host ports `80` and `5000` to the container, so the bare domains work without a port (`http://jpastack.local/`). If port `80` is already taken on your machine, use the `:5000` variants instead (`http://jpastack.local:5000/`).

### Troubleshooting (`site can't be reached`)

1. Is the container actually up? `docker compose ps` should show `flask` as running (not restarting).
2. Read the startup log: `docker compose logs --tail=50 flask`. A crash loop at import almost always means `app/.env` is missing — without `MONGO_URI` / `MONGO_DB` the app cannot start. Copy `app/.env.example` to `app/.env`, fill in real values, then `docker compose up -d --build`.
3. Bypass the custom domains first: `http://127.0.0.1:5000/` should return the site (unknown hosts skip domain routing). If that works but `http://jpastack.local/` doesn't, the `hosts` entries or port `80` mapping is the problem — check with `ping jpastack.local` (it must resolve to `127.0.0.1`).
4. If port `80` conflicts with another service, drop that mapping and use `http://jpastack.local:5000/`.

### Option B: Makefile shortcuts

- `make build` — `docker build -t flask_image .` (repo root is the build context)
- `make run` — run detached as `flask_app`: `-e PORT=5000 -p 5000:5000 --env-file app/.env` (override the port with `make run PORT=8080`)
- `make start-build-docker` — build + run
- `make stop` / `make remove` / `make restart` — stop / delete / recreate the `flask_app` container
- `make shell` — open bash inside the running container (`docker exec -it flask_app /bin/bash`)
- `make remove-image` — delete the `flask_image` image

### Option C: raw Docker commands

```bash
docker build -t flask_image .
docker run -d --name flask_app -p 5000:5000 -e PORT=5000 --env-file app/.env flask_image
docker logs -f flask_app
docker stop flask_app && docker rm flask_app
```

Notes:

- On Cloud Run / Render the platform injects `PORT` (e.g. `8080`); the image `CMD` binds `:$PORT`, so no code change is needed — just make sure the published port matches `PORT`.
- `make` targets also work in Windows Command Prompt; otherwise run the raw `docker` commands from Option C in cmd/PowerShell.

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
