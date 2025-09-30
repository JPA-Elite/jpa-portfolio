from flask import request, jsonify
from Services.VideoService import VideoService
from Repositories.VideoRepository import VideoRepository
from config import SortOrder, SortOrderStr
import json

# Initialize Services
video_service = VideoService(repository=VideoRepository())

# -------------------Administrator Controller------------------------
# Video Controller
def video_list_route():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    video_list, total_video = video_service.get_paginated_video_list(page, per_page, order)
    return jsonify({
        "video": [video.to_dict() for video in video_list],
        "total_video": total_video,
        "total_pages": (total_video + per_page - 1) // per_page,
    })

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
    return jsonify({"message": "Video added successfully", "video_id": video_id}), 201

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
        return jsonify({"message": "Video updated successfully"}), 200
    else:
        return jsonify({"message": "Failed to update video"}), 400

def delete_video_route(video_id):
    success = video_service.delete_video(video_id)
    if success:
        return jsonify({"message": "Video deleted successfully"}), 200
    else:
        return jsonify({"message": "Video not found"}), 404