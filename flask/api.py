# pages.py
from config import HTTPMethod as http
from flask import Blueprint
from Controllers.api.BaseController import change_language_route, delete_page_system_info_route, download_song_route, get_client_ip_route, profile_config_route, proxy_audio_route
from Controllers.api.MusicController import add_music_route, delete_music_route, music_list_route, update_music_route
from Controllers.api.VideoController import add_video_route, delete_video_route, update_video_route, video_list_route
from Controllers.api.GalleryController import add_gallery_route, delete_gallery_route, gallery_list_route, update_gallery_route
from Controllers.api.GalleryLikeController import add_gallery_like_route
from Controllers.api.DashboardController import visits_info_route
from Controllers.api.LoginAttemptController import login_attempt_list_route, delete_login_attempt_route
from Controllers.api.GalleryCommentController import gallery_comments_route, like_comment_route
from auth.middleware import admin_login_required
from Controllers.api.AuthController import update_profile_route

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

@api_bp.route("/api/proxy-audio")
def proxy_audio():
    return proxy_audio_route()

@api_bp.route("/api/music-list", methods=[http.GET])
def user_music_list():
    return music_list_route()


# ************************** Administroller API ********************************
# Dashboard API
@api_bp.route("/admin/api/visits/info", methods=[http.GET])
@admin_login_required
def visits_info():
    return visits_info_route()

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

@api_bp.route("/admin/api/update-profile", methods=[http.POST])
@admin_login_required
def update_profile():
    return update_profile_route()

@api_bp.route("/admin/api/delete-video/<video_id>", methods=[http.DELETE])
@admin_login_required
def delete_video(video_id):
    return delete_video_route(video_id)

# Gallery Likes API
@api_bp.route("/api/gallery-like", methods=[http.POST])
def add_gallery_like():
    return add_gallery_like_route()

# Gallery Comments API
@api_bp.route("/api/gallery-comments", methods=["GET", "POST"])
def gallery_comments():
    return gallery_comments_route()

@api_bp.route("/api/gallery-comments/like", methods=["POST"])
def like_comment():
    return like_comment_route()

# Login Attempt API
@api_bp.route("/admin/api/login-attempts", methods=[http.GET])
@admin_login_required
def login_attempts():
    return login_attempt_list_route()

@api_bp.route("/admin/api/delete-login-attempt/<login_attempt_id>", methods=[http.DELETE])
@admin_login_required
def delete_login_attempt(login_attempt_id):
    return delete_login_attempt_route(login_attempt_id)

# Other API
@api_bp.route("/admin/api/get-client-ip", methods=[http.GET])
@admin_login_required
def get_client_ip():
    return get_client_ip_route()