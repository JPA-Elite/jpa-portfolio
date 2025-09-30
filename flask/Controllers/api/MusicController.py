from flask import request, jsonify
from Services.MusicService import MusicService
from Repositories.MusicRepository import MusicRepository
from config import SortOrder, SortOrderStr

# Initialize Services
music_service = MusicService(repository=MusicRepository())

# -------------------Administrator Controller------------------------
# Music Controller
def music_list_route():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    music_list, total_music = music_service.get_paginated_music_list(page, per_page, order)

    return jsonify({
        "music": [music.to_dict() for music in music_list],
        "total_music": total_music,
        "total_pages": (total_music + per_page - 1) // per_page,
    })

def add_music_route():
    title = request.form.get("title")
    artist = request.form.get("artist")
    music_file = request.files.get("music_file")
    image_file = request.files.get("image_file")

    # Pass raw request data + files to service
    data = {
        "title": title,
        "artist": artist,
        "music_file": music_file,
        "image_file": image_file,
    }

    music_id = music_service.add_music(data)
    return jsonify({"message": "Music added successfully", "music_id": music_id}), 201

def update_music_route(music_id):
    title = request.form.get("title")
    artist = request.form.get("artist")
    music_file = request.files.get("music_file")
    image_file = request.files.get("image_file")

    update_data = {
        "title": title,
        "artist": artist,
        "music_file": music_file,
        "image_file": image_file,
    }

    success = music_service.update_music(music_id, update_data)
    if success:
        return jsonify({"message": "Music updated successfully"}), 200
    else:
        return jsonify({"message": "Failed to update music"}), 400

def delete_music_route(music_id):
    success = music_service.delete_music(music_id)
    if success:
        return jsonify({"message": "Music deleted successfully"}), 200
    else:
        return jsonify({"message": "Music not found"}), 404