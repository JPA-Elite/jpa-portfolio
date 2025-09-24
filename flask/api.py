# pages.py
from config import HTTPMethod
from flask import Blueprint
from Controllers.ApiController import add_portfolio_route, change_language_route, delete_page_system_info_route, download_song_route, profile_config_route

# Create a Blueprint for api
api_bp = Blueprint("api", __name__)

# ************************** API ********************************

@api_bp.route("/change_language/<lang_code>", methods=[HTTPMethod.GET])
def change_language(lang_code):
    return change_language_route(lang_code)

@api_bp.route("/add_portfolio", methods=[HTTPMethod.POST])
def add_portfolio():
    return add_portfolio_route()

@api_bp.route("/api/delete-page-system-info", methods=[HTTPMethod.DELETE])
def delete_page_system_info():
    return delete_page_system_info_route()

@api_bp.route("/api/profile-config", methods=[HTTPMethod.GET])
def profile_config():
    return profile_config_route()

@api_bp.route('/api/download_song')
def download_song():
    return download_song_route()