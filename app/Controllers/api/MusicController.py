from flask import jsonify
from app.Services.MusicService import MusicService
from app.Repositories.MusicRepository import MusicRepository
from app.configurations import SortOrder, SortOrderStr
from app.Requests.api.MusicRequest import MusicRequest
from app.constants.messages import MUSIC_ADD_MSG, MUSIC_DELETE_MSG, MUSIC_NOT_FOUND_ERROR, MUSIC_UPDATE_FAILED_ERROR, MUSIC_UPDATE_MSG
from app.Models.Music import Music

# Initialize Services
music_service = MusicService(repository=MusicRepository())

# -------------------Administrator Controller------------------------
# Music Controller
def music_list_route():
    form = MusicRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    page = data["page"]
    per_page = data["per_page"]
    search_query = data["search_query"]
    order = data["order"]
    category = data["category"]

    music_list, total_music = music_service.get_paginated_music_list(page, per_page, order, search_query, category)

    response_data = {
        "music": [music.to_dict() for music in music_list],
        "total_music": total_music,
        "total_pages": (total_music + per_page - 1) // per_page,
        "page": page,
        "per_page": per_page,
        "search": search_query,
        "category": category,
    }

    return jsonify(response_data)

def add_music_route():
    form = MusicRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    music_id = music_service.add_music(data)

    return jsonify({"message": MUSIC_ADD_MSG, "music_id": music_id}), 201

def update_music_route(music_id):
    form = MusicRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = music_service.update_music(music_id, data)
    if success:
        return jsonify({"message": MUSIC_UPDATE_MSG}), 200
    else:
        return jsonify({"message": MUSIC_UPDATE_FAILED_ERROR}), 400

def delete_music_route(music_id):
    form = MusicRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = music_service.delete_music(music_id)
    if success:
        return jsonify({"message": MUSIC_DELETE_MSG}), 200
    else:
        return jsonify({"message": MUSIC_NOT_FOUND_ERROR}), 404

def music_categories_route():
    """Get all categories with counts"""
    all_categories = Music.CATEGORIES
    counts = music_service.get_category_counts()
    categories = [c for c in all_categories if c]
    counts = {k: v for k, v in counts.items() if k}
    counts["All"] = music_service.get_total_music_count()
    return jsonify({"categories": categories, "counts": counts})
