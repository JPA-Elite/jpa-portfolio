# AGENTS.md

## Project overview

Flask + MongoDB portfolio app (server-rendered Jinja2, not SPA). Vite bundles JS/CSS for production.

## Quick commands

```bash
make package-install      # pip install -r app/requirements.txt
make start-build          # build frontend + run with dist assets
npm run dev               # Vite dev server + Flask concurrently
make start-local          # bare Flask (no Vite, no dist)
make test                 # python -m unittest discover -s tests -p "test_*.py"
make compile-translations # pybabel compile -d translations
```

## Frontend asset modes

- **Dev mode** (`npm run dev`): Vite on `:5173`, Flask proxies assets via `VITE_DEV_SERVER`. Templates get live-reload injected. Sets `VITE_DEV_SERVER=http://127.0.0.1:5173`.
- **Dist mode** (`make start-build` / `make start-local-dist`): Built assets served from `app/dist/frontend/`. Requires `FRONTEND_DIST=1 FRONTEND_DIST_TEMPLATES=1`.
- Use `static_asset('path/to/file.js')` in templates — it resolves to hashed filename in dist mode or Vite proxy URL in dev mode.

## Architecture

```
Routes (pages.py / api.py) → Controllers (Controllers/web, Controllers/api)
  → Services (Services/) → Repositories (Repositories/, extend BaseRepository)
```

- Controllers are plain functions, not classes. Routes use `HTTPMethod` enum.
- Repositories implement interfaces from `Repositories/Interfaces/`.
- Models are simple classes with `to_dict()` / `from_dict()`.
- Forms/validators in `Requests/`.
- All repos use `pymongo` directly — no ORM.

## Testing

- `unittest` framework; run with `make test`.
- Shared helpers: `tests/test_support.py` (DummyModel, FakeCursor, FakeCollection, dummy_repo_*).
- Repository tests: `tests/repositories/*/test_*.py` — use `_repository_test_helpers` for contract tests.
- Service tests: `tests/services/*/test_*.py` — use `MagicMock()` repos, fixtures from `_service_fixtures.py`.
- No integration / e2e tests. Tests are pure unit tests.

## Database

- MongoDB. Collection names in `constants/db_collections.py` (`MongoCollections`).
- Data migrations via `flask --app app/manage.py migrate <name> [--reset]`.

## Key patterns

- Caching: `@cache.cached(key_prefix=...)` on page routes; manual `cache.set/get/delete` in API controllers. `clear_cache_by_prefix()` utility.
- Translations: Flask-Babel with `_()` in templates. Locale from cookie `/lang`. Recompile with `make compile-translations`.
- Admin auth: session-based with `@admin_login_required` decorator. Face recognition + OTP are optional extra layers.
- Security: `app/security/ddos_guard.py` provides per-IP rate limiting. Configured via env vars in `.env.example`.
- Media uploads: Cloudinary. `cleanup_uploaded_files()` for rollback on failure.

## Notable constraints

- **No comments in code** (`.blackboxrules` enforces this).
- `Music.CATEGORIES` is a fixed list in the model.
- Do not rename DB collection names or table names.
- Mobile responsiveness required for all new pages.
