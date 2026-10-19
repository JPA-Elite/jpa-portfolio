from flask import Blueprint, Response, has_request_context, request
from datetime import datetime
import os

from app.seo import PROFESSIONAL_EXCLUDED_PAGES

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

PROFESSIONAL_PATHS = [
    path
    for path, page_key in PATH_PAGE_KEYS.items()
    if page_key not in PROFESSIONAL_EXCLUDED_PAGES
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
    professional_host = _config("PROFESSIONAL_DOMAIN")
    if professional_host in ("", landing_host):
        professional_host = ""
    landing_base = f"{scheme}://{landing_host}".rstrip("/")
    professional_base = f"{scheme}://{professional_host}".rstrip("/") if professional_host else ""
    return landing_base, professional_base


def generate_sitemap():
    lastmod = datetime.today().strftime('%Y-%m-%d')
    landing_base, professional_base = _resolve_bases()
    urls = [f"{landing_base}{path}" for path in PUBLIC_PATHS]
    if professional_base:
        urls.extend(f"{professional_base}{path}" for path in PROFESSIONAL_PATHS)
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
