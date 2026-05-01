# pages.py
from backend.Controllers.api.VlogCommentController import vlog_comments_route, vlog_like_comment_route
from backend.Controllers.api.VlogLikeController import (
    add_vlog_like_route,
    get_vlog_likes_count_route,
    get_vlog_likes_counts_batch_route,
)
from backend.configurations import HTTPMethod as http
from flask import Blueprint, request, request, jsonify, current_app
from datetime import datetime
import json
import os
from collections import deque
from backend.Controllers.api.BaseController import change_language_route, delete_page_system_info_route, download_song_route, get_client_ip_route, profile_config_route, proxy_audio_route
from backend.Repositories.ActivityLogRepository import ActivityLogRepository
from flask import session
from backend.Controllers.api.MusicController import add_music_route, delete_music_route, music_list_route, update_music_route
from backend.Controllers.api.KeyProjectController import (
    add_key_project_route,
    delete_key_project_route,
    key_project_list_route,
    update_key_project_route,
)
from backend.Controllers.api.CompanyRoadmapController import (
    add_company_roadmap_route,
    company_roadmap_list_route,
    delete_company_roadmap_route,
    update_company_roadmap_route,
)
from backend.Controllers.api.VideoController import add_video_route, delete_video_route, update_video_route, video_list_route
from backend.Controllers.api.GalleryController import add_gallery_route, delete_gallery_route, gallery_list_route, update_gallery_route
from backend.Controllers.api.GalleryLikeController import (
    add_gallery_like_route,
    get_gallery_likes_count_route,
    get_gallery_likes_counts_batch_route,
)
from backend.Controllers.api.DashboardController import visits_info_route, recent_activity_route, dashboard_summary_route, visits_list_route, visits_delete_route, recent_activity_delete_route
from backend.Repositories.MusicRepository import MusicRepository
from backend.Repositories.GalleryRepository import GalleryRepository
from backend.Repositories.VideoRepository import VideoRepository
from backend.Repositories.KeyProjectRepository import KeyProjectRepository
from backend.Repositories.CompanyRoadmapRepository import CompanyRoadmapRepository
from backend.Repositories.ActivityLogRepository import ActivityLogRepository
from backend.Controllers.api.LoginAttemptController import login_attempt_list_route, delete_login_attempt_route
from backend.Controllers.api.GalleryCommentController import gallery_comments_route, gallery_like_comment_route
from backend.auth.middleware import admin_login_required
from backend.Controllers.api.AuthController import update_profile_route

# Create a Blueprint for api
api_bp = Blueprint("api", __name__)


@api_bp.after_request
def _log_admin_activity(response):
    try:
        if request.path.startswith("/admin/api/") and request.method in ("POST", "PUT", "DELETE"):
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "remote_addr": request.remote_addr,
            }
            try:
                body = request.get_json(silent=True)
                if body:
                    entry["body"] = body
            except Exception:
                pass

            try:
                user_id = session.get("user_id")
                if user_id:
                    entry["user_id"] = user_id
            except Exception:
                pass

            try:
                repo = ActivityLogRepository()
                repo.insert(entry)
            except Exception:
                logs_dir = os.path.join(os.path.dirname(__file__), "logs")
                os.makedirs(logs_dir, exist_ok=True)
                logfile = os.path.join(logs_dir, "recent_activity.jsonl")
                with open(logfile, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        current_app.logger.exception("Failed to write admin activity log")
    return response

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

# Gallery Likes API
@api_bp.route("/api/gallery-like/counts", methods=[http.GET])
def get_gallery_likes_count():
    return get_gallery_likes_count_route()

@api_bp.route("/api/gallery-like/counts/batch", methods=[http.GET])
def get_gallery_likes_count_batch():
    return get_gallery_likes_counts_batch_route()

@api_bp.route("/api/gallery-like", methods=[http.POST])
def add_gallery_like():
    return add_gallery_like_route()

# Vlog Likes API
@api_bp.route("/api/vlog-like/counts", methods=[http.GET])
def get_vlog_likes_count():
    return get_vlog_likes_count_route()

@api_bp.route("/api/vlog-like/counts/batch", methods=[http.GET])
def get_vlog_likes_count_batch():
    return get_vlog_likes_counts_batch_route()

@api_bp.route("/api/vlog-like", methods=[http.POST])
def add_vlog_like():
    return add_vlog_like_route()

# Gallery Comments API
@api_bp.route("/api/gallery-comments", methods=[http.GET, http.POST])
def gallery_comments():
    return gallery_comments_route()

@api_bp.route("/api/gallery-comments/like", methods=[http.POST])
def like_comment():
    return gallery_like_comment_route()

# Vlog Comments API
@api_bp.route("/api/vlog-comments", methods=[http.GET, http.POST])
def vlog_comments():
    return vlog_comments_route()

@api_bp.route("/api/vlog-comments/like", methods=[http.POST])
def vlog_like_comment():
    return vlog_like_comment_route()


# ************************** Administroller API ********************************
# Dashboard API
@api_bp.route("/admin/api/visits/info", methods=[http.GET])
@admin_login_required
def visits_info():
    return visits_info_route()

@api_bp.route("/admin/api/visits-list", methods=[http.GET])
@admin_login_required
def visits_list():
    return visits_list_route()

@api_bp.route("/admin/api/delete-visits/<record_id>", methods=[http.DELETE])
@admin_login_required
def delete_visits(record_id):
    return visits_delete_route(record_id)

@api_bp.route("/admin/api/delete-activity", methods=[http.DELETE])
@admin_login_required
def delete_activity():
    ids = request.json.get("record_ids", []) if request.json else []
    return recent_activity_delete_route(ids)

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

# Key Projects API
@api_bp.route("/admin/api/key-project-list", methods=[http.GET])
@admin_login_required
def key_project_list():
    return key_project_list_route()

@api_bp.route("/admin/api/add-key-project", methods=[http.POST])
@admin_login_required
def add_key_project():
    return add_key_project_route()

@api_bp.route("/admin/api/update-key-project/<project_id>", methods=[http.PUT])
@admin_login_required
def update_key_project(project_id):
    return update_key_project_route(project_id)

@api_bp.route("/admin/api/delete-key-project/<project_id>", methods=[http.DELETE])
@admin_login_required
def delete_key_project(project_id):
    return delete_key_project_route(project_id)

# Company Roadmaps API
@api_bp.route("/admin/api/company-roadmap-list", methods=[http.GET])
@admin_login_required
def company_roadmap_list():
    return company_roadmap_list_route()

@api_bp.route("/admin/api/add-company-roadmap", methods=[http.POST])
@admin_login_required
def add_company_roadmap():
    return add_company_roadmap_route()

@api_bp.route("/admin/api/update-company-roadmap/<roadmap_id>", methods=[http.PUT])
@admin_login_required
def update_company_roadmap(roadmap_id):
    return update_company_roadmap_route(roadmap_id)

@api_bp.route("/admin/api/delete-company-roadmap/<roadmap_id>", methods=[http.DELETE])
@admin_login_required
def delete_company_roadmap(roadmap_id):
    return delete_company_roadmap_route(roadmap_id)

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

@api_bp.route("/admin/api/recent-activity", methods=[http.GET])
@admin_login_required
def recent_activity():
    return recent_activity_route()

@api_bp.route("/admin/api/dashboard-summary", methods=[http.GET])
@admin_login_required
def dashboard_summary():
    return dashboard_summary_route()
