import os
from flask import current_app, has_app_context, has_request_context, request


PUBLIC_PAGE_PATHS = frozenset({
    "/",
    "/profile",
    "/portfolio",
    "/gallery",
    "/vlog",
    "/music",
    "/concern",
    "/donation",
    "/build",
    "/booking",
    "/add_portfolio_form",
})

SHARED_EXACT_PATHS = frozenset({
    "/robots.txt",
    "/sitemap.xml",
    "/favicon.ico",
})

SHARED_PREFIXES = (
    "/static/",
    "/static",
    "/_vite/",
    "/_vite",
    "/_template_mtime",
    "/api/",
    "/api",
    "/change_language",
)

SITE_PROFESSIONAL = "professional"
SITE_SOCIAL = "social"
SITE_LANDING = "landing"
SITE_ADMIN = "admin"
SITE_UNKNOWN = "unknown"


def _env_bool_value(raw, default):
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def normalize_host(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    if "://" in text:
        text = text.split("://", 1)[1]
    text = text.split("/", 1)[0]
    text = text.split("@", 1)[-1]
    if text.startswith("["):
        end = text.find("]")
        if end != -1:
            text = text[: end + 1]
        return text.strip().rstrip(".")
    if text.count(":") == 1:
        host_part, port_part = text.rsplit(":", 1)
        if port_part.isdigit():
            text = host_part
    text = text.strip().rstrip(".")
    return text


def split_host_port(value):
    if value is None:
        return "", ""
    text = str(value).strip()
    if not text:
        return "", ""
    if "@" in text:
        text = text.rsplit("@", 1)[-1]
    if text.startswith("["):
        end = text.find("]")
        if end == -1:
            return text.lower(), ""
        host = text[: end + 1]
        rest = text[end + 1:]
        if rest.startswith(":") and rest[1:].isdigit():
            return host.lower(), rest[1:]
        return host.lower(), ""
    if text.count(":") == 1:
        host_part, port_part = text.rsplit(":", 1)
        if port_part.isdigit() and host_part:
            return host_part.strip().lower().rstrip("."), port_part
    return text.strip().lower().rstrip("."), ""


def _resolve_setting(name, default=""):
    if has_app_context():
        try:
            value = current_app.config.get(name, None)
        except Exception:
            value = None
        if value is None or (isinstance(value, str) and not value.strip()):
            value = os.getenv(name, default)
        return value if value is not None else default
    return os.getenv(name, default)


def get_domain_config():
    landing = normalize_host(_resolve_setting("LANDING_DOMAIN", ""))
    professional = normalize_host(_resolve_setting("PROFESSIONAL_DOMAIN", ""))
    social = normalize_host(_resolve_setting("SOCIAL_DOMAIN", ""))
    admin = normalize_host(_resolve_setting("ADMIN_DOMAIN", ""))
    raw_enabled = _resolve_setting("DOMAIN_ROUTING_ENABLED", "true")
    if isinstance(raw_enabled, bool):
        enabled = raw_enabled
    else:
        enabled = _env_bool_value(raw_enabled, True)
    return {
        "landing_domain": landing,
        "professional_domain": professional,
        "social_domain": social,
        "admin_domain": admin,
        "routing_enabled": enabled,
    }


def landing_hosts(config=None):
    cfg = config or get_domain_config()
    hosts = set()
    for key in ("landing_domain", "professional_domain", "social_domain"):
        value = (cfg.get(key) or "").strip().lower()
        if value:
            hosts.add(value)
    return hosts


def current_site(host=None):
    if host is None:
        if has_request_context():
            host = request.host
        else:
            host = ""
    normalized = normalize_host(host)
    if not normalized:
        return SITE_UNKNOWN
    cfg = get_domain_config()
    if cfg.get("professional_domain") and normalized == cfg["professional_domain"]:
        return SITE_PROFESSIONAL
    if cfg.get("admin_domain") and normalized == cfg["admin_domain"]:
        return SITE_ADMIN
    if cfg.get("social_domain") and normalized == cfg["social_domain"]:
        return SITE_SOCIAL
    if cfg.get("landing_domain") and normalized == cfg["landing_domain"]:
        return SITE_LANDING
    return SITE_UNKNOWN


def is_admin_path(path):
    if not path:
        return False
    return path == "/admin" or path.startswith("/admin/")


def is_shared_path(path):
    if not path:
        return False
    if path in SHARED_EXACT_PATHS:
        return True
    for prefix in SHARED_PREFIXES:
        if path == prefix or path.startswith(prefix if prefix.endswith("/") else prefix + "/"):
            return True
        if path.startswith(prefix):
            if prefix in ("/static", "/_vite", "/api"):
                return True
    return False


def is_public_page(path):
    if not path:
        return False
    if path in PUBLIC_PAGE_PATHS:
        return True
    return False


def build_cross_host_url(target_host, path, query_string="", scheme="http", port=""):
    target = normalize_host(target_host)
    if not target:
        return None
    if not path or not path.startswith("/"):
        path = "/" + str(path or "")
    host_with_port = target
    clean_port = str(port or "").strip()
    if clean_port and ":" not in target and clean_port not in ("80", "443"):
        host_with_port = f"{target}:{clean_port}"
    query = ""
    if isinstance(query_string, (bytes, bytearray)):
        try:
            query = bytes(query_string).decode()
        except Exception:
            query = ""
    else:
        query = str(query_string or "")
    query = query.lstrip("?")
    use_scheme = (scheme or "http").strip().lower() or "http"
    if query:
        return f"{use_scheme}://{host_with_port}{path}?{query}"
    return f"{use_scheme}://{host_with_port}{path}"


def skip_cache_on_professional_host():
    if has_request_context():
        try:
            return current_site(request.host) == SITE_PROFESSIONAL
        except Exception:
            return False
    return False


def resolve_domain_redirect(host, path, query_string="", scheme="http", method="GET"):
    cfg = get_domain_config()
    if not cfg.get("routing_enabled"):
        return None
    normalized, port = split_host_port(host)
    if not normalized:
        return None
    landings = landing_hosts(cfg)
    admin = cfg.get("admin_domain") or ""
    is_known = normalized in landings or (admin and normalized == admin)
    if not is_known:
        return None
    if is_shared_path(path):
        return None
    if normalized in landings and is_admin_path(path):
        if admin and admin != normalized:
            return build_cross_host_url(admin, path, query_string, scheme, port)
        return None
    if admin and normalized == admin and is_public_page(path):
        canonical = cfg.get("landing_domain") or cfg.get("social_domain") or cfg.get("professional_domain") or ""
        if canonical and canonical != normalized:
            return build_cross_host_url(canonical, path, query_string, scheme, port)
        return None
    return None


def get_request_site():
    if has_request_context():
        return current_site(request.host)
    return SITE_UNKNOWN
