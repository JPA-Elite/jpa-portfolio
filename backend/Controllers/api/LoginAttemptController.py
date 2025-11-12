from flask import request, jsonify
from Services.LoginAttemptService import LoginAttemptService
from Repositories.LoginAttemptRepository import LoginAttemptRepository
from config import SortOrder, SortOrderStr
from utils import clear_cache_by_prefix, get_cache_data
from extensions import cache

# Initialize Services
login_attempt_service = LoginAttemptService(repository=LoginAttemptRepository())

# -------------------Administrator Controller------------------------
# LoginAttempt Controller
def login_attempt_list_route():
    cached_data, cache_key = get_cache_data("admin.api.login_attempt_list", request.args, 60)
    if cached_data:
        return jsonify(cached_data)

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    login_attempt_list, total_login_attempt = login_attempt_service.get_paginated_login_attempt_list(page, per_page, order)

    response_data = {
        "login_attempt": [login_attempt.to_dict() for login_attempt in login_attempt_list],
        "total_login_attempt": total_login_attempt,
        "total_pages": (total_login_attempt + per_page - 1) // per_page,
    }

    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)


def delete_login_attempt_route(login_attempt_id):
    success = login_attempt_service.delete_login_attempt(login_attempt_id)
    if success:
        clear_cache_by_prefix("admin.api.login_attempt_list:")
        return jsonify({"message": "Login Attempt deleted successfully"}), 200
    else:
        return jsonify({"message": "Login Attempt not found"}), 404