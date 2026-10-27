from flask import Blueprint, Response, has_request_context, request
from datetime import datetime
from urllib.parse import quote
import os

from app.domains import SITE_PROFESSIONAL, SITE_SOCIAL, current_site

sitemap_bp = Blueprint("sitemap", __name__)

PRODUCTION_HOST = "jpastack.com"

PUBLIC_PATHS = [
    "/",
    "/portfolio",
    "/gallery",
    "/vlog",
    "/music",
    "/concern",
    "/donation",
    "/build",
]

PATH_PAGE_KEYS = {
    "/portfolio": "portfolio",
    "/gallery": "gallery",
    "/vlog": "vlog",
    "/music": "music",
    "/concern": "concern",
    "/donation": "donation",
    "/build": "build",
}

PROFESSIONAL_SITEMAP_PAGES = frozenset({"portfolio", "build"})

PROFESSIONAL_PATHS = [
    path
    for path, page_key in PATH_PAGE_KEYS.items()
    if page_key in PROFESSIONAL_SITEMAP_PAGES
]

APP_DETAILS_PREFIX = "/apps/"


def _active_built_app_slugs():
    try:
        from app.Repositories.BuiltAppRepository import BuiltAppRepository
        from app.Services.BuiltAppService import BuiltAppService

        service = BuiltAppService(repository=BuiltAppRepository())
        slugs = []
        for built_app in service.get_active_built_apps():
            slug = str(getattr(built_app, "slug", "") or "").strip().lower()
            if slug:
                slugs.append(slug)
        return slugs
    except Exception:
        return []


def _built_app_paths():
    return [
        f"{APP_DETAILS_PREFIX}{quote(slug, safe='-._~')}"
        for slug in _active_built_app_slugs()
        if slug
    ]


def _resolve_bases():
    scheme = "https"
    request_host = ""
    if has_request_context():
        try:
            scheme = (request.scheme or "https").strip().lower() or "https"
        except Exception:
            scheme = "https"
        try:
            request_host = (request.host or "").strip().lower()
        except Exception:
            request_host = ""
        if ":" in request_host:
            host_part, _, port_part = request_host.rpartition(":")
            if port_part.isdigit() and host_part:
                request_host = host_part

    def _config(name):
        try:
            from flask import current_app, has_app_context
            if has_app_context():
                value = current_app.config.get(name, "")
                if value and str(value).strip():
                    return str(value).strip().lower()
        except Exception:
            pass
        return (os.getenv(name, "") or "").strip().lower()

    landing_host = _config("LANDING_DOMAIN") or request_host or PRODUCTION_HOST
    professional_host = _config("PROFESSIONAL_DOMAIN") or landing_host
    social_host = _config("SOCIAL_DOMAIN") or landing_host
    professional_base = f"{scheme}://{professional_host}".rstrip("/")
    social_base = f"{scheme}://{social_host}".rstrip("/")
    return social_base, professional_base


def generate_sitemap():
    lastmod = datetime.today().strftime('%Y-%m-%d')
    social_base, professional_base = _resolve_bases()
    site = ""
    if has_request_context():
        try:
            site = current_site(request.host)
        except Exception:
            site = ""
    if site == SITE_SOCIAL:
        urls = [f"{social_base}{path}" for path in PUBLIC_PATHS + _built_app_paths()]
    elif site == SITE_PROFESSIONAL:
        urls = [f"{professional_base}{path}" for path in PROFESSIONAL_PATHS + _built_app_paths()]
    else:
        urls = [f"{professional_base}{path}" for path in PROFESSIONAL_PATHS]
    entries = "\n".join(
        f"""        <url>
            <loc>{url}</loc>
            <lastmod>{lastmod}</lastmod>
        </url>"""
        for url in urls
    )
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
    </urlset>"""
    
    return Response(sitemap_xml, mimetype="application/xml")

@sitemap_bp.route("/sitemap.xml")
def sitemap():
    return generate_sitemap()
