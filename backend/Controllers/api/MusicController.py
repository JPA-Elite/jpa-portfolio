from flask import request, jsonify
from Services.MusicService import MusicService
from Repositories.MusicRepository import MusicRepository
from configurations import SortOrder, SortOrderStr
from constants.messages import MUSIC_ADD_MSG, MUSIC_DELETE_MSG, MUSIC_NOT_FOUND_ERROR, MUSIC_UPDATE_FAILED_ERROR, MUSIC_UPDATE_MSG
from utils import clear_cache_by_prefix, get_cache_data
from extensions import cache

# Initialize Services
music_service = MusicService(repository=MusicRepository())

# -------------------Administrator Controller------------------------
# Music Controller
def music_list_route():
    cached_data, cache_key = get_cache_data("admin.api.music_list", request.args)
    if cached_data:
        return jsonify(cached_data)

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search_query = (request.args.get("search") or "").strip()
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    music_list, total_music = music_service.get_paginated_music_list(page, per_page, order, search_query)

    response_data = {
        "music": [music.to_dict() for music in music_list],
        "total_music": total_music,
        "total_pages": (total_music + per_page - 1) // per_page,
        "page": page,
        "per_page": per_page,
        "search": search_query,
    }

    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)

def add_music_route():
    title = request.form.get("title")
    artist = request.form.get("artist")
    lyrics = request.form.get("lyrics", "")
    music_file = request.files.get("music_file")
    image_file = request.files.get("image_file")

    # Pass raw request data + files to service
    data = {
        "title": title,
        "artist": artist,
        "lyrics": lyrics,
        "music_file": music_file,
        "image_file": image_file,
    }

    music_id = music_service.add_music(data)

    clear_cache_by_prefix("admin.api.music_list:")
    return jsonify({"message": MUSIC_ADD_MSG, "music_id": music_id}), 201

def update_music_route(music_id):
    title = request.form.get("title")
    artist = request.form.get("artist")
    lyrics = request.form.get("lyrics")
    music_file = request.files.get("music_file")
    image_file = request.files.get("image_file")

    update_data = {
        "title": title,
        "artist": artist,
        "lyrics": lyrics,
        "music_file": music_file,
        "image_file": image_file,
    }

    success = music_service.update_music(music_id, update_data)
    if success:
        clear_cache_by_prefix("admin.api.music_list:")
        return jsonify({"message": MUSIC_UPDATE_MSG}), 200
    else:
        return jsonify({"message": MUSIC_UPDATE_FAILED_ERROR}), 400

def delete_music_route(music_id):
    success = music_service.delete_music(music_id)
    if success:
        clear_cache_by_prefix("admin.api.music_list:")
        return jsonify({"message": MUSIC_DELETE_MSG}), 200
    else:
        return jsonify({"message": MUSIC_NOT_FOUND_ERROR}), 404
