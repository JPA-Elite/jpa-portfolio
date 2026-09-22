from flask import request, jsonify
from app.Services.BuiltAppLikeService import BuiltAppLikeService
from app.Repositories.BuiltAppLikeRepository import BuiltAppLikeRepository
from app.Requests.api.BuiltAppLikeRequest import BuiltAppLikeRequest

built_app_like_service = BuiltAppLikeService(repository=BuiltAppLikeRepository())

def built_app_like_counts_route():
    form = BuiltAppLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    client_ip = data["client_ip"]
    app_id = data["app_id"]

    like_counts = built_app_like_service.get_likes_count(app_id)
    dislike_counts = built_app_like_service.get_dislikes_count(app_id)
    existing_vote = built_app_like_service.get_user_vote(app_id, client_ip)

    return jsonify({
        "like_counts": like_counts,
        "dislike_counts": dislike_counts,
        "user_vote": existing_vote.get("is_like") if existing_vote else None
    }), 200

def built_app_toggle_vote_route():
    form = BuiltAppLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    app_id = data["app_id"]
    is_like = data["is_like"]
    client_ip = data["client_ip"]

    result = built_app_like_service.toggle_vote(app_id, client_ip, bool(is_like))
    return jsonify({"message": "Vote updated", "data": result}), 200
