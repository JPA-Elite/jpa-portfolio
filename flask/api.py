# pages.py
from config import HTTPMethod as http
from flask import Blueprint
from Controllers.api.BaseController import change_language_route, delete_page_system_info_route, download_song_route, profile_config_route
from Controllers.api.MusicController import add_music_route, delete_music_route, music_list_route, update_music_route
from Controllers.api.VideoController import add_video_route, delete_video_route, update_video_route, video_list_route
from Controllers.api.GalleryController import add_gallery_route, delete_gallery_route, gallery_list_route, update_gallery_route
from auth.middleware import admin_login_required

# Create a Blueprint for api
api_bp = Blueprint("api", __name__)

# ************************** PUBLIC API ********************************

@api_bp.route("/change_language/<lang_code>", methods=[http.GET])
def change_language(lang_code):
    return change_language_route(lang_code)

@api_bp.route("/api/delete-page-system-info", methods=[http.DELETE])
def delete_page_system_info():
    return delete_page_system_info_route()

@api_bp.route("/api/profile-config", methods=[http.GET])
def profile_config():
    return profile_config_route()

@api_bp.route('/api/download_song')
def download_song():
    return download_song_route()


# ************************** Administroller API ********************************
# Music API
@api_bp.route("/admin/api/music-list", methods=[http.GET])
@admin_login_required
def music_list():
    return music_list_route()

@api_bp.route("/admin/api/add-music", methods=[http.POST])
@admin_login_required
def add_music():
    return add_music_route()

@api_bp.route("/admin/api/update-music/<music_id>", methods=[http.PUT])
@admin_login_required
def update_music(music_id):
    return update_music_route(music_id)

@api_bp.route("/admin/api/delete-music/<music_id>", methods=[http.DELETE])
@admin_login_required
def delete_music(music_id):
    return delete_music_route(music_id)

# Gallery API
@api_bp.route("/admin/api/gallery-list", methods=[http.GET])
@admin_login_required
def gallery_list():
    return gallery_list_route()

@api_bp.route("/admin/api/add-gallery", methods=[http.POST])
@admin_login_required
def add_gallery():
    return add_gallery_route()

@api_bp.route("/admin/api/update-gallery/<gallery_id>", methods=[http.PUT])
@admin_login_required
def update_gallery(gallery_id):
    return update_gallery_route(gallery_id)

@api_bp.route("/admin/api/delete-gallery/<gallery_id>", methods=[http.DELETE])
@admin_login_required
def delete_gallery(gallery_id):
    return delete_gallery_route(gallery_id)

# Video API
@api_bp.route("/admin/api/video-list", methods=[http.GET])
@admin_login_required
def video_list():
    return video_list_route()

@api_bp.route("/admin/api/add-video", methods=[http.POST])
@admin_login_required
def add_video():
    return add_video_route()

@api_bp.route("/admin/api/update-video/<video_id>", methods=[http.PUT])
@admin_login_required
def update_video(video_id):
    return update_video_route(video_id)

@api_bp.route("/admin/api/delete-video/<video_id>", methods=[http.DELETE])
@admin_login_required
def delete_video(video_id):
    return delete_video_route(video_id)