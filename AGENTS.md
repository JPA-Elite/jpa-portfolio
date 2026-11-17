# AGENTS.md

## Project overview

Flask + MongoDB portfolio app (server-rendered Jinja2, not SPA). Vite bundles JS/CSS for production.

## Quick commands

```bash
make package-install      # py -3.11 -m pip install -r app/requirements.txt
make start-build          # build frontend + run with dist assets
npm run dev               # Vite dev server + Flask concurrently
make start-local          # bare Flask (no Vite, no dist)
make test                 # backend unit tests + Playwright frontend specs
make compile-translations # pybabel compile -d translations
```

## Frontend asset modes

- **Dev mode** (`npm run dev`): Vite on `:5173`, Flask proxies assets via `VITE_DEV_SERVER`. Templates get live-reload injected. Sets `VITE_DEV_SERVER=http://127.0.0.1:5173`. Also runs the SCSS watcher.
- **Dist mode** (`make start-build` / `make start-local-dist`): Built assets served from `app/dist/frontend/`. Requires `FRONTEND_DIST=1 FRONTEND_DIST_TEMPLATES=1`.
- Use `static_asset('path/to/file.js')` in templates — it resolves to hashed filename in dist mode or Vite proxy URL in dev mode.

## Styles (SCSS)

- First-party styles are authored as SCSS in `app/static/scss/` and compiled to `app/static/css/` (git-ignored) by `node scripts/build-styles.mjs`.
- `make css-build` compiles once; `make css-watch` / `npm run css:watch` recompiles on change. `npm run dev`, `make start-local*`, `make start-build`, `make run-docker-local` and the Playwright `webServer` compile first.
- Compiled output mirrors the source path (`scss/pages/x.scss` → `css/pages/x.css`), so `url(...)` values and `scripts/page-bundles.json` entries keep working.
- Shared tokens, functions and mixins live in `app/static/scss/abstracts/` (`@use "abstracts" as *;`). Prefer them over raw hex/sizes in new code.
- `app/static/scss/themes.scss` stays the runtime theme API (`:root[data-theme]` custom properties); SCSS variables are authoring-only.
- Vendor CSS stays plain CSS and is never converted: `app/static/css/bootstrap/`, `app/static/css/plyr/`, `app/static/css/pages/admin/adminlte*.css`.
- Use `@use`/`@forward`, never `@import`. Keep `calc()` inside `min()`/`max()`/`clamp()` wrapped as `#{calc(...)}` so the compiler does not rewrite it.
- Never hand-edit files in `app/static/css/` — edit the matching `app/static/scss/` source and rebuild.

## Architecture

```
Routes (routes/pages.py, routes/api.py) → Controllers (Controllers/web, Controllers/api)
  → Services (Services/) → Repositories (Repositories/, extend BaseRepository)
```

- Controllers are plain functions, not classes. Routes use `HTTPMethod` enum.
- Repositories implement interfaces from `Repositories/Interfaces/`.
- Models are simple classes with `to_dict()` / `from_dict()`.
- Forms/validators in `Requests/` (includes `LoginForm.py`).
- All repos use `pymongo` directly — no ORM.

Key packages:

```
app/core/       HTTPMethod/HTTPStatus/SortOrder enums, locale config, response helpers, i18n text maps
app/routes/     blueprints and route wiring (pages, api, sitemap)
app/site/       hostname/domain routing and SEO metadata
app/security/   admin login, DDoS guard, hCaptcha, admin_login_required decorator
app/utils/      pagination/filtering, cache helpers, Cloudinary/media, filenames, streaming
```

- `app/app.py` builds the Flask app, `app/manage.py` is the CLI entrypoint, `app/extensions.py` holds shared singletons (`cache`).
- Controllers return response helpers from `app/core/responses.py` (`json_response`, `ok_response`, `message_response`, ...) instead of calling `jsonify` directly.

## Testing

- `unittest` framework; run with `make test`.
- Shared helpers: `tests/test_support.py` (DummyModel, FakeCursor, FakeCollection, dummy_repo_*).
- Repository tests: `tests/repositories/*/test_*.py` — use `_repository_test_helpers` for contract tests.
- Service tests: `tests/services/*/test_*.py` — use `MagicMock()` repos, fixtures from `_service_fixtures.py`.
- No integration / e2e tests. Tests are pure unit tests.
- **Test file whitespace**: every backend (`tests/**/*.py`) and frontend (`tests/frontend/**/*.js`) test file must use a **single blank line** between classes, functions and methods — never two or more consecutive blank lines — with no trailing spaces/tabs and exactly one newline at end of file. Only blank lines may be adjusted; never re-indent code, and never strip spaces inside intentional test data strings (e.g. `"   "`, `"  Joshua  "`, `" ,  , "`), since those are part of the assertions.
- **Matching test scope**: when adding or updating a test, keep the new file consistent with these rules and run `make test` (or `python scripts/run_tests.py` for backend only) before finishing.

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
- **Always keep mobile responsive when changing desktop code**: every desktop-view change (CSS, templates, JS) must also verify the mobile breakpoints (`1024px`, `900px`, `768px`, `480px`) still render without overflow or overlap. Never leave a desktop-only layout unhandled on small screens.
- **Never modify the cache key_prefix names in `app/routes/pages.py`** (e.g. `portfolio_ui_v10_{get_locale()}...`, `vlog_ui_v37_...`, `gallery_ui_v34_...`). Keep the version numbers/names exactly as they are.
- **Never build the frontend** (`npm run build:frontend` / `make start-build`) to save time — edit source files only.
- **Clean up temp files**: whenever you create temporary files (scratch files, scripts, etc.), delete them once all the changes are done and verified.
