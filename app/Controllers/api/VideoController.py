from app.Services.VideoService import VideoService
from app.Repositories.VideoRepository import VideoRepository
from app.core.configurations import SortOrder, SortOrderStr, HTTPStatus as status
from app.core.responses import created_response, json_response, message_response
from app.Requests.api.VideoRequest import VideoRequest
from app.constants.messages import VIDEO_ADD_MSG, VIDEO_DELETE_MSG, VIDEO_NOT_FOUND_ERROR, VIDEO_UPDATE_FAILED_ERROR, VIDEO_UPDATE_MSG
from app.utils.cache import clear_cache_by_prefix

# Initialize Services
video_service = VideoService(repository=VideoRepository())

# -------------------Administrator Controller------------------------
# Video Controller
def video_list_route():
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

    return json_response(response_data)

def add_video_route():
    form = VideoRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    video_id = video_service.add_video(data)
    clear_cache_by_prefix("vlog_")
    return created_response(VIDEO_ADD_MSG, video_id=video_id)

def update_video_route(video_id):
    form = VideoRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = video_service.update_video(video_id, data)
    if success:
        clear_cache_by_prefix("vlog_")
        return message_response(VIDEO_UPDATE_MSG)
    else:
        return message_response(VIDEO_UPDATE_FAILED_ERROR, status.BAD_REQUEST)

def delete_video_route(video_id):
    form = VideoRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = video_service.delete_video(video_id)
    if success:
        clear_cache_by_prefix("vlog_")
        return message_response(VIDEO_DELETE_MSG)
    else:
        return message_response(VIDEO_NOT_FOUND_ERROR, status.NOT_FOUND)
