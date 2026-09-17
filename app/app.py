from flask import Flask, g, redirect, render_template, request, send_from_directory, url_for, Response, abort
from app.configurations import (
    ERROR_404_PAGE,
    LANGUAGES,
    BABEL_DEFAULT_LOCALE,
    EN_LOCALE,
    CEB_LOCALE,
    TL_LOCALE,
    get_locale,
)
from flask_babel import Babel
from app.pages import pages_bp
from app.api import api_bp
from datetime import datetime, timedelta
import json
from app.sitemap import sitemap_bp
import os
import requests
from markupsafe import Markup
import time
from werkzeug.middleware.proxy_fix import ProxyFix
from app.extensions import cache
from app.domains import current_site, get_domain_config, resolve_domain_redirect
from app.security import init_ddos_guard
from dotenv import load_dotenv

def _env_bool(name: str, default: bool):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

load_dotenv()

if os.getenv("FLASK_DEBUG") is None and os.getenv("FLASK_ENV"):
    os.environ["FLASK_DEBUG"] = "1" if os.getenv("FLASK_ENV", "").lower() == "development" else "0"
os.environ.pop("FLASK_ENV", None)

app_root = os.path.dirname(__file__)
default_templates = os.path.join(app_root, "templates")
default_static = os.path.join(app_root, "static")
dist_root = os.path.join(app_root, "dist", "frontend")
dist_templates = os.path.join(dist_root, "templates")
dist_static = os.path.join(dist_root, "static")
use_frontend_dist = _env_bool("FRONTEND_DIST", False)
use_dist_static = use_frontend_dist and os.path.isdir(dist_static)
use_dist_templates = (
    use_frontend_dist
    and _env_bool("FRONTEND_DIST_TEMPLATES", False)
    and os.path.isdir(dist_templates)
)

app = Flask(
    __name__,
    template_folder=dist_templates if use_dist_templates else default_templates,
    static_folder=dist_static if use_dist_static else default_static,
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
app.config["LANGUAGES"] = LANGUAGES
app.config["BABEL_DEFAULT_LOCALE"] = BABEL_DEFAULT_LOCALE
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
app.config["SESSION_COOKIE_SECURE"] = _env_bool(
    "SESSION_COOKIE_SECURE",
    not _env_bool("FLASK_DEBUG", False),
)

app.config["CACHE_TYPE"] = os.getenv("CACHE_TYPE", "simple")
try:
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "86400"))
except (TypeError, ValueError):
    app.config["CACHE_DEFAULT_TIMEOUT"] = 86400

cache_redis_url = os.getenv("CACHE_REDIS_URL")
if cache_redis_url:
    app.config["CACHE_REDIS_URL"] = cache_redis_url

cache_key_prefix = os.getenv("CACHE_KEY_PREFIX")
if cache_key_prefix:
    app.config["CACHE_KEY_PREFIX"] = cache_key_prefix

app.config["LANDING_DOMAIN"] = os.getenv("LANDING_DOMAIN", "")
app.config["PROFESSIONAL_DOMAIN"] = os.getenv("PROFESSIONAL_DOMAIN", "")
app.config["SOCIAL_DOMAIN"] = os.getenv("SOCIAL_DOMAIN", "")
app.config["ADMIN_DOMAIN"] = os.getenv("ADMIN_DOMAIN", "")
app.config["DOMAIN_ROUTING_ENABLED"] = _env_bool("DOMAIN_ROUTING_ENABLED", True)

app.register_blueprint(pages_bp)
app.register_blueprint(sitemap_bp)
app.register_blueprint(api_bp)


@app.before_request
def enforce_domain_routing():
    try:
        raw_query = request.query_string.decode()
    except Exception:
        raw_query = ""
    try:
        target = resolve_domain_redirect(
            request.host,
            request.path,
            raw_query,
            request.scheme,
            request.method,
        )
    except Exception:
        target = None
    if target:
        code = 301 if request.method in ("GET", "HEAD") else 307
        return redirect(target, code=code)
    try:
        g.site = current_site(request.host)
    except Exception:
        g.site = "unknown"


@app.context_processor
def inject_site_domains():
    try:
        cfg = get_domain_config()
    except Exception:
        cfg = {
            "landing_domain": "",
            "professional_domain": "",
            "social_domain": "",
            "admin_domain": "",
        }
    try:
        site = current_site(request.host)
    except Exception:
        site = "unknown"
    return dict(
        landing_domain=cfg.get("landing_domain", ""),
        professional_domain=cfg.get("professional_domain", ""),
        social_domain=cfg.get("social_domain", ""),
        admin_domain=cfg.get("admin_domain", ""),
        current_site=site,
    )

_asset_manifest_cache = {"mtime": None, "data": {}}
_vite_dev_server = os.getenv("VITE_DEV_SERVER", "").strip()
_vite_proxy_assets = _env_bool("VITE_PROXY_ASSETS", False)
_template_livereload = _env_bool("TEMPLATE_LIVERELOAD", False) or bool(_vite_dev_server)
_template_mtime_cache = {"checked": 0.0, "mtime": 0.0}

def _vite_asset_url(path: str):
    base = _vite_dev_server.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _load_asset_manifest():
    manifest_path = os.path.join(app.static_folder or "", "manifest.json")
    if not os.path.isfile(manifest_path):
        _asset_manifest_cache["mtime"] = None
        _asset_manifest_cache["data"] = {}
        return {}
    mtime = os.path.getmtime(manifest_path)
    if _asset_manifest_cache["mtime"] == mtime:
        return _asset_manifest_cache["data"]
    try:
        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError):
        _asset_manifest_cache["mtime"] = None
        _asset_manifest_cache["data"] = {}
        return {}
    asset_map = {}
    for key, entry in manifest.items():
        if isinstance(entry, str):
            file_name = entry
            src_name = None
        else:
            file_name = entry.get("file")
            src_name = entry.get("src")
        if file_name:
            asset_map[str(key).lstrip("/")] = file_name
            if src_name:
                asset_map[str(src_name).lstrip("/")] = file_name
    _asset_manifest_cache["mtime"] = mtime
    _asset_manifest_cache["data"] = asset_map
    return asset_map


def static_asset(path: str):
    if not path:
        return ""
    clean_path = path.lstrip("/")
    if _vite_dev_server:
        if _vite_proxy_assets:
            return url_for("vite_proxy", asset_path=clean_path)
        return _vite_asset_url(clean_path)
    asset_map = _load_asset_manifest()
    mapped = asset_map.get(clean_path)
    if mapped:
        return url_for("static", filename=mapped)
    return url_for("static", filename=clean_path)


def vite_hmr():
    if not _vite_dev_server:
        return ""
    src = static_asset("@vite/client")
    return Markup(f'<script type="module" src="{src}"></script>')


def _latest_template_mtime():
    root = app.template_folder or ""
    if not root or not os.path.isdir(root):
        return 0.0
    now = time.time()
    if now - _template_mtime_cache["checked"] < 1.0:
        return _template_mtime_cache["mtime"]
    latest = 0.0
    for dirpath, dirnames, filenames in os.walk(root):
        if "__pycache__" in dirnames:
            dirnames.remove("__pycache__")
        for name in filenames:
            if not name.endswith(".html"):
                continue
            try:
                mtime = os.path.getmtime(os.path.join(dirpath, name))
            except OSError:
                continue
            if mtime > latest:
                latest = mtime
    _template_mtime_cache["checked"] = now
    _template_mtime_cache["mtime"] = latest
    return latest


def template_livereload():
    if not _template_livereload:
        return ""
    return Markup(
        "<script>"
        "(function(){"
        "var last=0;"
        "async function check(){"
        "try{"
        "var res=await fetch('/_template_mtime',{cache:'no-store'});"
        "var txt=await res.text();"
        "var cur=Number(txt)||0;"
        "if(last&&cur>last){location.reload();return;}"
        "last=cur;"
        "}catch(e){}"
        "}"
        "setInterval(check,1000);"
        "check();"
        "})();"
        "</script>"
    )


cache.init_app(app)
init_ddos_guard(app)

babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)

@app.after_request
@app.after_request
def remove_csp(response):
    response.headers.pop("Content-Security-Policy", None)
    return response

@app.context_processor
def inject_locale():
    return dict(get_locale=get_locale)

@app.context_processor
def inject_static_asset():
    return dict(static_asset=static_asset)

@app.context_processor
def inject_vite_hmr():
    return dict(vite_hmr=vite_hmr)

@app.context_processor
def inject_template_livereload():
    return dict(template_livereload=template_livereload)

@app.context_processor
def inject_hcaptcha():
    return dict(
        HCAPTCHA_SITE_KEY=os.getenv("HCAPTCHA_SITE_KEY"),
        HCAPTCHA_ENABLED=os.getenv("HCAPTCHA_ENABLED", "true").lower() not in ("false", "0", "no", "off"),
    )


if _vite_dev_server:
    @app.route("/_vite/<path:asset_path>")
    def vite_proxy(asset_path):
        target = _vite_asset_url(asset_path)
        try:
            resp = requests.get(target, timeout=10)
        except requests.RequestException:
            abort(502)
        excluded = {"content-encoding", "transfer-encoding", "connection"}
        headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]
        return Response(resp.content, status=resp.status_code, headers=headers)

if _template_livereload:
    @app.route("/_template_mtime")
    def template_mtime():
        return Response(str(_latest_template_mtime()), mimetype="text/plain")


# ************************** LOCALE CONTANTS ********************************

@app.context_processor
def en_locale():
    return dict(en_locale=EN_LOCALE)


@app.context_processor
def ceb_locale():
    return dict(ceb_locale=CEB_LOCALE)


@app.context_processor
def tl_locale():
    return dict(tl_locale=TL_LOCALE)

@app.context_processor
def inject_now():
    return dict(now=datetime.now())

@app.context_processor
def inject_preset_avatars():
    from app.constants.avatars import DEFAULT_AVATAR_URL, PRESET_AVATARS
    return dict(
        default_avatar_url=DEFAULT_AVATAR_URL,
        preset_avatars=PRESET_AVATARS,
    )


@app.context_processor
def inject_profile_image():
    from app.configurations import PROFILE_IMAGE
    return dict(profile_image=PROFILE_IMAGE)

@app.errorhandler(404)
def not_found(error):
    return render_template(ERROR_404_PAGE, title="Not Found", error=error), 404

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')


@app.template_filter()
def truncate_text(text, length=120):
    if text and len(text) > length:
        return text[:length] + " ..."
    return text

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
