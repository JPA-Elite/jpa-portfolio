# pages.py
from flask import Blueprint, request
from backend.configurations import HTTPMethod as http, get_locale
from backend.auth.middleware import admin_login_required, server_login_required
from backend.Controllers.web.PageController import add_portfolio_form_route, concern_route, device_info_route, donation_route, gallery_route, index_route, music_route, profile_route, vlog_route
from backend.Controllers.web.AdminPageController import admin_company_roadmaps_route, admin_dashboard_route, admin_gallery_route, admin_key_projects_route, admin_login_attempts_route, admin_login_route, admin_logout_route, admin_music_route, admin_settings_route, admin_video_route, admin_server_users_route, admin_server_channels_route
from backend.Controllers.web.ServerPageController import (
    server_app_route,
    server_entry_route,
    server_forgot_password_route,
    server_login_route,
    server_logout_route,
    server_register_route,
    server_settings_route,
)
from backend.extensions import cache

# Create a Blueprint for pages
pages_bp = Blueprint("pages", __name__)

# ************************** PAGES ********************************
@pages_bp.route("/", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"index_{get_locale()}_{request.query_string.decode()}")
def index():
    return index_route()

@pages_bp.route("/profile", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"profile_ui_v10_{get_locale()}_{request.query_string.decode()}")
def profile():
    return profile_route()

@pages_bp.route("/gallery", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"gallery_ui_v9_{get_locale()}_{request.query_string.decode()}")
def gallery():
    return gallery_route()

@pages_bp.route("/vlog", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"vlog_ui_v12_{get_locale()}_{request.query_string.decode()}")
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

@pages_bp.route("/server", methods=[http.GET])
def server_entry():
    return server_entry_route()

@pages_bp.route("/server/login", methods=[http.GET, http.POST])
def server_login():
    return server_login_route()

@pages_bp.route("/server/register", methods=[http.GET, http.POST])
def server_register():
    return server_register_route()

@pages_bp.route("/server/forgot-password", methods=[http.GET, http.POST])
def server_forgot_password():
    return server_forgot_password_route()

@pages_bp.route("/server/app", methods=[http.GET])
@server_login_required
def server_app():
    return server_app_route()

@pages_bp.route("/server/settings", methods=[http.GET, http.POST])
@server_login_required
def server_settings():
    return server_settings_route()

@pages_bp.route("/server/logout", methods=[http.GET])
@server_login_required
def server_logout():
    return server_logout_route()


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
@cache.cached(key_prefix="admin_page_dashboard")
def admin_dashboard():
    return admin_dashboard_route()

@pages_bp.route("/admin/gallery", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_gallery")
def admin_gallery():
    return admin_gallery_route()

@pages_bp.route("/admin/video", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_video")
def admin_video():
    return admin_video_route()

@pages_bp.route("/admin/music", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_music")
def admin_music():
    return admin_music_route()

@pages_bp.route("/admin/key-projects", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_key_projects")
def admin_key_projects():
    return admin_key_projects_route()

@pages_bp.route("/admin/company-roadmaps", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_company_roadmaps")
def admin_company_roadmaps():
    return admin_company_roadmaps_route()

@pages_bp.route("/admin/settings", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_settings")
def admin_settings():
    return admin_settings_route()

@pages_bp.route("/admin/login-attempts", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_login_attempts")
def admin_login_attempts():
    return admin_login_attempts_route()

@pages_bp.route("/admin/server-users", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_server_users")
def admin_server_users():
    return admin_server_users_route()

@pages_bp.route("/admin/server-channels", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_server_channels")
def admin_server_channels():
    return admin_server_channels_route()
