from flask import request, jsonify
from app.Services.MusicLikeService import MusicLikeService
from app.Repositories.MusicLikeRepository import MusicLikeRepository
from app.Requests.api.MusicLikeRequest import MusicLikeRequest

music_like_service = MusicLikeService(repository=MusicLikeRepository())

def music_like_counts_route():
    form = MusicLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    client_ip = data["client_ip"]
    music_id = data["music_id"]

    like_counts = music_like_service.get_likes_count(music_id)
    dislike_counts = music_like_service.get_dislikes_count(music_id)
    existing_vote = music_like_service.get_user_vote(music_id, client_ip)

    return jsonify({
        "like_counts": like_counts,
        "dislike_counts": dislike_counts,
        "user_vote": existing_vote.get("is_like") if existing_vote else None
    }), 200

def music_like_counts_batch_route():
    form = MusicLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    client_ip = data["client_ip"]
    music_ids = data["music_ids"]

    if not music_ids:
        return jsonify({"items": {}}), 200

    like_counts = music_like_service.get_likes_counts_by_ids(music_ids)
    dislike_counts = music_like_service.get_dislikes_counts_by_ids(music_ids)

    items = {}
    for mid in music_ids:
        vote = music_like_service.get_user_vote(mid, client_ip)
        items[mid] = {
            "like_counts": like_counts.get(mid, 0),
            "dislike_counts": dislike_counts.get(mid, 0),
            "user_vote": vote.get("is_like") if vote else None
        }

    return jsonify({"items": items}), 200

def music_toggle_vote_route():
    form = MusicLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    music_id = data["music_id"]
    is_like = data["is_like"]
    client_ip = data["client_ip"]

    result = music_like_service.toggle_vote(music_id, client_ip, bool(is_like))
    return jsonify({"message": "Vote updated", "data": result}), 200
