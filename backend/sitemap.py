from flask import Blueprint, Response
from datetime import datetime
from backend.constants.app_defaults import SITEMAP_BASE_URL

sitemap_bp = Blueprint("sitemap", __name__)

def generate_sitemap():
    lastmod = datetime.today().strftime('%Y-%m-%d')
    base_url = SITEMAP_BASE_URL

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>{base_url}/</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
        <url>
            <loc>{base_url}/profile</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
        <url>
            <loc>{base_url}/gallery</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
        <url>
            <loc>{base_url}/vlog</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
        <url>
            <loc>{base_url}/concern</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
        <url>
            <loc>{base_url}/donation</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
        <url>
            <loc>{base_url}/music</loc>
            <lastmod>{lastmod}</lastmod>
        </url>
    </urlset>"""
    
    return Response(sitemap_xml, mimetype="application/xml")

@sitemap_bp.route("/sitemap.xml")
def sitemap():
    return generate_sitemap()
