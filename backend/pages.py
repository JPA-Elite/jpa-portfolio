# pages.py
from flask import Blueprint, request
from configurations import HTTPMethod as http, get_locale
from auth.middleware import admin_login_required
from Controllers.web.PageController import add_portfolio_form_route, concern_route, device_info_route, donation_route, gallery_route, index_route, music_route, profile_route, vlog_route
from Controllers.web.AdminPageController import admin_dashboard_route, admin_gallery_route, admin_login_attempts_route, admin_login_route, admin_logout_route, admin_music_route, admin_settings_route, admin_video_route
from extensions import cache

# Create a Blueprint for pages
pages_bp = Blueprint("pages", __name__)

# ************************** PAGES ********************************
@pages_bp.route("/", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"index_{get_locale()}_{request.query_string.decode()}")
def index():
    return index_route()

@pages_bp.route("/profile", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"profile_{get_locale()}_{request.query_string.decode()}")
def profile():
    return profile_route()

@pages_bp.route("/gallery", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"gallery_{get_locale()}_{request.query_string.decode()}")
def gallery():
    return gallery_route()

@pages_bp.route("/vlog", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"vlog_{get_locale()}_{request.query_string.decode()}")
def vlog():
    return vlog_route()

@pages_bp.route("/music", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"music_{get_locale()}_{request.query_string.decode()}")
def music():
    return music_route()

@pages_bp.route("/concern", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"concern_{get_locale()}_{request.query_string.decode()}")
def concern():
    return concern_route()

@pages_bp.route("/donation", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"donation_{get_locale()}_{request.query_string.decode()}")
def donation():
    return donation_route()

@pages_bp.route("/device-info/visits", methods=[http.GET])
def device_info():
    return device_info_route()

@pages_bp.route("/add_portfolio_form", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"add_portfolio_form_{get_locale()}_{request.query_string.decode()}")
def add_portfolio_form():
    return add_portfolio_form_route()


# ************************** ADMIN PAGES ********************************
@pages_bp.route("/admin/login", methods=[http.GET, http.POST])
def admin_login():
    return admin_login_route()

@pages_bp.route("/admin/logout", methods=[http.GET])
@admin_login_required
def admin_logout():
    return admin_logout_route()

@pages_bp.route("/admin/dashboard", methods=[http.GET])
@admin_login_required
@cache.cached()
def admin_dashboard():
    return admin_dashboard_route()

@pages_bp.route("/admin/gallery", methods=[http.GET])
@admin_login_required
@cache.cached()
def admin_gallery():
    return admin_gallery_route()

@pages_bp.route("/admin/video", methods=[http.GET])
@admin_login_required
@cache.cached()
def admin_video():
    return admin_video_route()

@pages_bp.route("/admin/music", methods=[http.GET])
@admin_login_required
@cache.cached()
def admin_music():
    return admin_music_route()

@pages_bp.route("/admin/settings", methods=[http.GET])
@admin_login_required
@cache.cached()
def admin_settings():
    return admin_settings_route()

@pages_bp.route("/admin/login-attempts", methods=[http.GET])
@admin_login_required
@cache.cached()
def admin_login_attempts():
    return admin_login_attempts_route()