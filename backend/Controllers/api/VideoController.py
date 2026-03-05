from flask import request, jsonify
from backend.Services.VideoService import VideoService
from backend.Repositories.VideoRepository import VideoRepository
from backend.configurations import SortOrder, SortOrderStr
import json
from backend.constants.messages import VIDEO_ADD_MSG, VIDEO_DELETE_MSG, VIDEO_NOT_FOUND_ERROR, VIDEO_UPDATE_FAILED_ERROR, VIDEO_UPDATE_MSG
from backend.utils import clear_cache_by_prefix, get_cache_data
from backend.extensions import cache

# Initialize Services
video_service = VideoService(repository=VideoRepository())

# -------------------Administrator Controller------------------------
# Video Controller
def video_list_route():
    cached_data, cache_key = get_cache_data("admin.api.video_list", request.args)
    if cached_data:
        return jsonify(cached_data)

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search_query = (request.args.get("search") or "").strip()
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    if search_query:
        video_list, total_video = video_service.search_video_paginated(
            search_query,
            None,
            "en",
            page,
            per_page,
            order,
        )
    else:
        video_list, total_video = video_service.get_paginated_video_list(page, per_page, order)

    response_data = {
        "video": [video.to_dict() for video in video_list],
        "total_video": total_video,
        "total_pages": (total_video + per_page - 1) // per_page,
        "search": search_query,
    }

    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)

def add_video_route():
    title = request.form.get("title")
    description = request.form.get("description")
    video_file = request.files.get("video_file")
    tags = request.form.get("tags")
    # Pass raw request data + files to service
    data = {
        "title": json.loads(title) if title else {},
        "description": json.loads(description) if description else {},
        "video_file": video_file,
        "tags": json.loads(tags) if tags else [],
    }

    video_id = video_service.add_video(data)
    clear_cache_by_prefix("admin.api.video_list:")
    clear_cache_by_prefix("vlog_")
    return jsonify({"message": VIDEO_ADD_MSG, "video_id": video_id}), 201

def update_video_route(video_id):
    title = request.form.get("title")
    description = request.form.get("description")
    video_file = request.files.get("video_file")
    tags = request.form.get("tags")

    update_data = {
        "title": json.loads(title) if title else {},
        "description": json.loads(description) if description else {},
        "video_file": video_file,
        "tags": json.loads(tags) if tags else [],
    }

    success = video_service.update_video(video_id, update_data)
    if success:
        clear_cache_by_prefix("admin.api.video_list:")
        clear_cache_by_prefix("vlog_")
        return jsonify({"message": VIDEO_UPDATE_MSG}), 200
    else:
        return jsonify({"message": VIDEO_UPDATE_FAILED_ERROR}), 400

def delete_video_route(video_id):
    success = video_service.delete_video(video_id)
    if success:
        clear_cache_by_prefix("admin.api.video_list:")
        clear_cache_by_prefix("vlog_")
        return jsonify({"message": VIDEO_DELETE_MSG}), 200
    else:
        return jsonify({"message": VIDEO_NOT_FOUND_ERROR}), 404
