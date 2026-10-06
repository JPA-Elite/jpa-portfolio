from flask import jsonify
from app.Services.LoginAttemptService import LoginAttemptService
from app.Repositories.LoginAttemptRepository import LoginAttemptRepository
from app.configurations import SortOrder, SortOrderStr
from app.Requests.api.LoginAttemptRequest import LoginAttemptRequest
from app.constants.messages import LOGIN_ATTEMPT_DELETE_MSG, LOGIN_ATTEMPT_NOT_FOUND_ERROR

# Initialize Services
login_attempt_service = LoginAttemptService(repository=LoginAttemptRepository())

# -------------------Administrator Controller------------------------
# LoginAttempt Controller
def login_attempt_list_route():
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

    return jsonify(response_data)

def delete_login_attempt_route(login_attempt_id):
    form = LoginAttemptRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = login_attempt_service.delete_login_attempt(login_attempt_id)
    if success:
        return jsonify({"message": LOGIN_ATTEMPT_DELETE_MSG}), 200
    else:
        return jsonify({"message": LOGIN_ATTEMPT_NOT_FOUND_ERROR}), 404

