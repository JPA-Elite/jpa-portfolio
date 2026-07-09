from flask import request, jsonify
from app.Services.LoginAttemptService import LoginAttemptService
from app.Repositories.LoginAttemptRepository import LoginAttemptRepository
from app.configurations import SortOrder, SortOrderStr
from app.Requests.api.LoginAttemptRequest import LoginAttemptRequest
from app.constants.messages import LOGIN_ATTEMPT_DELETE_MSG, LOGIN_ATTEMPT_NOT_FOUND_ERROR
from app.utils import clear_cache_by_prefix, get_cache_data
from app.extensions import cache

# Initialize Services
login_attempt_service = LoginAttemptService(repository=LoginAttemptRepository())

# -------------------Administrator Controller------------------------
# LoginAttempt Controller
def login_attempt_list_route():
    cached_data, cache_key = get_cache_data("admin.api.login_attempt_list", request.args, 60)
    if cached_data:
        return jsonify(cached_data)

    form = LoginAttemptRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    login_attempt_list, total_login_attempt = login_attempt_service.get_paginated_login_attempt_list(
        data["page"],
        data["per_page"],
        data["order"],
        data["search_query"],
    )

    response_data = {
        "login_attempt": [login_attempt.to_dict() for login_attempt in login_attempt_list],
        "total_login_attempt": total_login_attempt,
        "total_pages": (total_login_attempt + data["per_page"] - 1) // data["per_page"],
        "search": data["search_query"],
    }

    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)

def delete_login_attempt_route(login_attempt_id):
    form = LoginAttemptRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = login_attempt_service.delete_login_attempt(login_attempt_id)
    if success:
        clear_cache_by_prefix("admin.api.login_attempt_list:")
        return jsonify({"message": LOGIN_ATTEMPT_DELETE_MSG}), 200
    else:
        return jsonify({"message": LOGIN_ATTEMPT_NOT_FOUND_ERROR}), 404

