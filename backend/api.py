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
from bson import ObjectId
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
from backend.Controllers.api.DashboardController import visits_info_route, recent_activity_route, dashboard_summary_route, visits_list_route, visits_delete_route, recent_activity_delete_route, clear_all_visitors_route, clear_all_activity_route
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

@api_bp.route("/admin/api/clear-all-visitors", methods=[http.DELETE])
@admin_login_required
def clear_all_visitors():
    return clear_all_visitors_route()

@api_bp.route("/admin/api/clear-all-activity", methods=[http.DELETE])
@admin_login_required
def clear_all_activity():
    return clear_all_activity_route()

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


# ********************* Admin Face Recognition (server-side) *********************
# This is a functional implementation using:
# - OpenCV Haar cascade to detect + crop face from uploaded image
# - A simple grayscale resize-based hash to compare reference vs new capture
# - Stored in users doc under: face_reference_hash and face_reference_crop_b64

import base64
import cv2  # type: ignore
import numpy as np  # type: ignore
import hashlib  # stdlib

from backend.Repositories.AuthRepository import AuthRepository

_auth_repo_for_faces = AuthRepository()
_FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def _require_image_b64(payload: dict) -> str:
    if not payload:
        raise ValueError("Missing JSON body")
    b64 = payload.get("image_b64")
    if not b64 or not isinstance(b64, str):
        raise ValueError("Missing image_b64")
    return b64


def _decode_b64_image(image_b64: str) -> np.ndarray:
    # Accept either raw base64 or data URL format
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    raw = base64.b64decode(image_b64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img


def _detect_and_crop_face(img_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if faces is None or len(faces) == 0:
        raise ValueError("No face detected")
    # Take the largest face (then expand box slightly to be more tolerant to head position)
    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])

    x0 = max(0, int(x - 0.15 * w))
    y0 = max(0, int(y - 0.15 * h))
    x1 = min(gray.shape[1], int(x + w + 0.15 * w))
    y1 = min(gray.shape[0], int(y + h + 0.15 * h))

    face = gray[y0:y1, x0:x1]
    if face.size == 0:
        raise ValueError("Invalid face crop")

    # Resize + normalize to a stable representation for comparison
    face_resized = cv2.resize(face, (160, 160))
    return face_resized


def _normalize_face(face_gray_160: np.ndarray) -> np.ndarray:
    # Normalize size + blur to reduce sensitivity to noise.
    blur = cv2.GaussianBlur(face_gray_160, (5, 5), 0)
    normalized = cv2.resize(blur, (160, 160))
    return normalized.astype(np.uint8)


def _encode_crop_to_b64(face_gray_160: np.ndarray) -> str:
    # Encode cropped face to PNG bytes and base64 them for storage (optional)
    ok, png = cv2.imencode(".png", face_gray_160)
    if not ok:
        raise ValueError("Could not encode face crop")
    return base64.b64encode(png.tobytes()).decode("utf-8")


def _face_l1_distance(a_gray_160: np.ndarray, b_gray_160: np.ndarray) -> float:
    # Mean absolute difference in pixel space (0..255), lower is more similar.
    a = a_gray_160.astype(np.float32)
    b = b_gray_160.astype(np.float32)
    return float(np.mean(np.abs(a - b)))


def _b64_png_to_gray_160(face_crop_b64: str) -> np.ndarray:
    if not face_crop_b64 or not isinstance(face_crop_b64, str):
        raise ValueError("Missing stored face reference")
    raw = base64.b64decode(face_crop_b64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode stored face reference")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if gray.shape != (160, 160):
        gray = cv2.resize(gray, (160, 160))
    return gray.astype(np.uint8)


@api_bp.route("/admin/api/face/register", methods=[http.POST])
@admin_login_required
def admin_face_register():
    try:
        payload = request.get_json(silent=True) or {}

        # Accept either single capture (image_b64) or multiple captures (image_b64_list)
        image_b64_list = payload.get("image_b64_list")
        if isinstance(image_b64_list, list) and len(image_b64_list) > 0:
            b64_list = [x for x in image_b64_list if isinstance(x, str)]
        else:
            b64_list = [_require_image_b64(payload)]

        if not b64_list:
            return jsonify({"ok": False, "message": "Missing image captures"}), 400

        crops = []
        for image_b64 in b64_list:
            img = _decode_b64_image(image_b64)
            face_crop = _detect_and_crop_face(img)  # grayscale 160x160
            face_crop_norm = _normalize_face(face_crop)
            crops.append(face_crop_norm)

        if not crops:
            return jsonify({"ok": False, "message": "No valid face crops captured"}), 400

        # Robust reference: pixel-wise median across captures
        reference_gray_160 = np.median(np.stack(crops, axis=0), axis=0).astype(np.uint8)
        face_crop_b64 = _encode_crop_to_b64(reference_gray_160)

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        # Store only the reference crop (tolerant matching uses it)
        _auth_repo_for_faces.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "face_reference_crop_b64": face_crop_b64,
                # overwrite hash too for backwards compatibility / debugging
                "face_reference_hash": "",
                "face_last_registered_at": datetime.utcnow().isoformat() + "Z",
            }},
            upsert=False,
        )
        return jsonify({"ok": True, "message": "Face reference registered"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


# ********************* Admin OTP (Email) *********************
# OTP is used to replace face verification in the admin login flow.
from backend.Services.OtpService import OtpService


@api_bp.route("/admin/api/otp/send", methods=[http.POST])
@admin_login_required
def admin_otp_send():
    try:
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip()

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        svc = OtpService()

        # If the client doesn't provide an email, use the one saved on the admin user document.
        if not email:
            try:
                user_doc = AuthRepository().find_by_id(str(user_id)) or {}
                email = (user_doc.get("email") or "").strip()
            except Exception:
                email = ""

        if not email:
            return jsonify({"ok": False, "message": "OTP email not configured. Please set it in Admin Settings."}), 400

        msg = svc.send_otp(user_id=str(user_id), email=email)
        return jsonify({"ok": True, "message": msg})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@api_bp.route("/admin/api/otp/verify", methods=[http.POST])
@admin_login_required
def admin_otp_verify():
    try:
        payload = request.get_json(silent=True) or {}
        otp = (payload.get("otp") or "").strip()

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        if not otp:
            return jsonify({"ok": False, "message": "Missing otp."}), 400

        svc = OtpService()
        result = svc.verify_otp(user_id=str(user_id), otp=otp)

        if not result.get("ok"):
            retry_after = result.get("retry_after_seconds")
            attempts_remaining = result.get("attempts_remaining")

            status_code = 403
            if result.get("reason") == "cooldown":
                status_code = 429

            return (
                jsonify(
                    {
                        "ok": False,
                        "message": result.get("message") or "Invalid/expired OTP.",
                        "reason": result.get("reason"),
                        "retry_after_seconds": retry_after,
                        "attempts_remaining": attempts_remaining,
                    }
                ),
                status_code,
            )

        session["face_verified"] = True
        return jsonify({"ok": True, "message": "OTP verified"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@api_bp.route("/admin/api/otp/reset", methods=[http.POST])
@admin_login_required
def admin_otp_reset():
    try:
        # Clear OTP/face gate so the OTP modal can be shown again.
        session.pop("face_verified", None)
        return jsonify({"ok": True, "message": "OTP verification gate cleared"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@api_bp.route("/admin/api/otp/email", methods=[http.GET])
@admin_login_required
def admin_otp_email_get():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        user_doc = AuthRepository().find_by_id(str(user_id)) or {}
        email = (user_doc.get("email") or "").strip()

        svc = OtpService()
        retry_after_seconds = svc.get_cooldown_remaining_seconds(str(user_id))
        response = {
            "ok": True,
            "email": email,
            "retry_after_seconds": retry_after_seconds,
            "message": (
                f"Too many invalid attempts. Please wait {retry_after_seconds} seconds and try again."
                if retry_after_seconds and retry_after_seconds > 0
                else ""
            ),
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@api_bp.route("/admin/api/otp/email", methods=[http.POST])
@admin_login_required
def admin_otp_email_save():
    try:
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip()

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        if not email:
            return jsonify({"ok": False, "message": "Missing email."}), 400

        AuthRepository().update_user(str(user_id), {"email": email})
        return jsonify({"ok": True, "message": "OTP email updated"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@api_bp.route("/admin/api/face/records", methods=[http.GET])
@admin_login_required
def admin_face_records():
    """
    Return face verification records for the logged-in admin.

    The UI currently expects rows to show:
    - Status (Registered / Verified)
    - Distance (if verified)
    - Timestamp (registered/verified time)
    """
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        user_doc = _auth_repo_for_faces.collection.find_one({"_id": ObjectId(user_id)}) or {}

        registered_at = user_doc.get("face_last_registered_at")
        verified_at = user_doc.get("face_last_verified_at")
        distance = user_doc.get("face_last_verify_distance")

        rows = []

        if registered_at:
            rows.append({
                "status": "Registered",
                "distance": None,
                "timestamp": registered_at,
            })

        if verified_at:
            rows.append({
                "status": "Verified",
                "distance": distance,
                "timestamp": verified_at,
            })

        # Keep stable ordering: Registered first, then Verified
        return jsonify({"ok": True, "rows": rows})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@api_bp.route("/admin/api/face/verify", methods=[http.POST])
@admin_login_required
def admin_face_verify():
    try:
        payload = request.get_json(silent=True) or {}

        # Accept either single capture (image_b64) or multiple captures (image_b64_list)
        image_b64_list = payload.get("image_b64_list")
        if isinstance(image_b64_list, list) and len(image_b64_list) > 0:
            b64_list = [x for x in image_b64_list if isinstance(x, str)]
        else:
            b64_list = [_require_image_b64(payload)]

        if not b64_list:
            return jsonify({"ok": False, "message": "Missing image captures"}), 400

        crops = []
        for image_b64 in b64_list:
            img = _decode_b64_image(image_b64)
            face_crop = _detect_and_crop_face(img)  # grayscale 160x160
            face_crop_norm = _normalize_face(face_crop)
            crops.append(face_crop_norm)

        if not crops:
            return jsonify({"ok": False, "message": "No valid face crops captured"}), 400

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        user_doc = _auth_repo_for_faces.collection.find_one({"_id": ObjectId(user_id)})
        ref_crop_b64 = (user_doc or {}).get("face_reference_crop_b64")
        if not ref_crop_b64:
            return jsonify({"ok": False, "message": "No registered face found. Please register first."}), 400

        ref_gray_160 = _b64_png_to_gray_160(ref_crop_b64)

        # Robust verify: take the minimum distance among captured frames
        distances = [_face_l1_distance(crop, ref_gray_160) for crop in crops]
        dist = float(min(distances))

        # Tune threshold: higher = more tolerant. Starting point.
        THRESHOLD_L1 = 22.0
        if dist > THRESHOLD_L1:
            return jsonify({
                "ok": False,
                "message": "Face does not match. Please try again.",
                "distance": dist
            }), 403

        _auth_repo_for_faces.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "face_last_verified_at": datetime.utcnow().isoformat() + "Z",
                "face_last_verify_distance": dist,
            }},
            upsert=False,
        )

        session["face_verified"] = True
        return jsonify({"ok": True, "message": "Face verified", "distance": dist})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400
