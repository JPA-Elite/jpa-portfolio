# pages.py
from flask import Blueprint
from Controllers.PageController import add_portfolio_form_route, concern_route, device_info_route, donation_route, gallery_route, index_route, music_route, profile_route, vlog_route
from Controllers.AdminPageController import admin_dashboard_route

# Create a Blueprint for pages
pages_bp = Blueprint("pages", __name__)

# ************************** PAGES ********************************


@pages_bp.route("/")
def index():
    return index_route()

@pages_bp.route("/profile")
def profile():
    return profile_route()

@pages_bp.route("/gallery")
def gallery():
    return gallery_route()

@pages_bp.route("/vlog")
def vlog():
    return vlog_route()

@pages_bp.route("/music")
def music():
    return music_route()

@pages_bp.route("/concern")
def concern():
    return concern_route()

@pages_bp.route("/donation")
def donation():
    return donation_route()

@pages_bp.route("/device-info/visits")
def device_info():
    return device_info_route()

@pages_bp.route("/add_portfolio_form")
def add_portfolio_form():
    return add_portfolio_form_route()

# ************************** ADMIN PAGES ********************************
@pages_bp.route("/admin/dashboard")
def admin_dashboard():
    return admin_dashboard_route()
