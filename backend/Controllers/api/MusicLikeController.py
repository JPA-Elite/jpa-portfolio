from flask import request, jsonify
from backend.Services.MusicLikeService import MusicLikeService
from backend.Repositories.MusicLikeRepository import MusicLikeRepository
from backend.utils import clear_cache_by_prefix

music_like_service = MusicLikeService(repository=MusicLikeRepository())

def music_like_counts_route():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    music_id = request.args.get("music_id", "")

    like_counts = music_like_service.get_likes_count(music_id)
    dislike_counts = music_like_service.get_dislikes_count(music_id)
    existing_vote = music_like_service.get_user_vote(music_id, client_ip)

    return jsonify({
        "like_counts": like_counts,
        "dislike_counts": dislike_counts,
        "user_vote": existing_vote.get("is_like") if existing_vote else None
    }), 200

def music_like_counts_batch_route():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    raw_ids = request.args.get("music_ids", "")
    music_ids = [mid.strip() for mid in raw_ids.split(",") if mid.strip()][:50]

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
    data = request.get_json(silent=True) or {}
    music_id = data.get("music_id")
    is_like = data.get("is_like", True)
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not music_id:
        return jsonify({"error": "Missing music_id"}), 400

    result = music_like_service.toggle_vote(music_id, client_ip, bool(is_like))
    return jsonify({"message": "Vote updated", "data": result}), 200
