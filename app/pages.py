# pages.py
from flask import Blueprint, request
from app.configurations import HTTPMethod as http, get_locale
from app.auth.middleware import admin_login_required
from app.Controllers.web.PageController import add_portfolio_form_route, booking_route, concern_route, donation_route, gallery_route, index_route, music_route, portfolio_redirect, profile_route, vlog_route
from app.Controllers.web.AdminPageController import admin_booking_requests_route, admin_company_roadmaps_route, admin_dashboard_route, admin_face_recognition_route, admin_gallery_route, admin_key_projects_route, admin_login_attempts_route, admin_login_route, admin_logout_route, admin_music_route, admin_settings_route, admin_video_route
from app.extensions import cache

# Create a Blueprint for pages
pages_bp = Blueprint("pages", __name__)

# ************************** PAGES ********************************
@pages_bp.route("/", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"index_{get_locale()}_{request.query_string.decode()}")
def index():
    return index_route()

@pages_bp.route("/profile", methods=[http.GET])
def profile():
    return portfolio_redirect()

@pages_bp.route("/portfolio", methods=[http.GET])
@cache.cached(key_prefix=lambda: f"portfolio_ui_v10_{get_locale()}_{request.query_string.decode()}")
def portfolio():
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

@pages_bp.route("/booking", methods=[http.GET])
def booking():
    return booking_route()

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
def admin_settings():
    return admin_settings_route()

@pages_bp.route("/admin/login-attempts", methods=[http.GET])
@admin_login_required
@cache.cached(key_prefix="admin_page_login_attempts")
def admin_login_attempts():
    return admin_login_attempts_route()


@pages_bp.route("/admin/booking-requests", methods=[http.GET])
@admin_login_required
def admin_booking_requests():
    return admin_booking_requests_route()

@pages_bp.route("/admin/face-recognition", methods=[http.GET, http.POST])
@admin_login_required
def admin_face_recognition():
    return admin_face_recognition_route()
