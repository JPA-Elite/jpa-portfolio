from flask import request, jsonify
from app.Services.VideoService import VideoService
from app.Repositories.VideoRepository import VideoRepository
from app.configurations import SortOrder, SortOrderStr
from app.Requests.api.VideoRequest import VideoRequest
from app.constants.messages import VIDEO_ADD_MSG, VIDEO_DELETE_MSG, VIDEO_NOT_FOUND_ERROR, VIDEO_UPDATE_FAILED_ERROR, VIDEO_UPDATE_MSG
from app.utils import clear_cache_by_prefix, get_cache_data
from app.extensions import cache

# Initialize Services
video_service = VideoService(repository=VideoRepository())

# -------------------Administrator Controller------------------------
# Video Controller
def video_list_route():
    cached_data, cache_key = get_cache_data("admin.api.video_list", request.args)
    if cached_data:
        return jsonify(cached_data)

    form = VideoRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    page = data["page"]
    per_page = data["per_page"]
    search_query = data["search_query"]
    order = data["order"]

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
    form = VideoRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    video_id = video_service.add_video(data)
    clear_cache_by_prefix("admin.api.video_list:")
    clear_cache_by_prefix("vlog_")
    return jsonify({"message": VIDEO_ADD_MSG, "video_id": video_id}), 201

def update_video_route(video_id):
    form = VideoRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = video_service.update_video(video_id, data)
    if success:
        clear_cache_by_prefix("admin.api.video_list:")
        clear_cache_by_prefix("vlog_")
        return jsonify({"message": VIDEO_UPDATE_MSG}), 200
    else:
        return jsonify({"message": VIDEO_UPDATE_FAILED_ERROR}), 400

def delete_video_route(video_id):
    form = VideoRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = video_service.delete_video(video_id)
    if success:
        clear_cache_by_prefix("admin.api.video_list:")
        clear_cache_by_prefix("vlog_")
        return jsonify({"message": VIDEO_DELETE_MSG}), 200
    else:
        return jsonify({"message": VIDEO_NOT_FOUND_ERROR}), 404

