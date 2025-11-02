from flask import request, jsonify
from Services.LoginAttemptService import LoginAttemptService
from Repositories.LoginAttemptRepository import LoginAttemptRepository
from config import SortOrder, SortOrderStr

# Initialize Services
login_attempt_service = LoginAttemptService(repository=LoginAttemptRepository())

# -------------------Administrator Controller------------------------
# LoginAttempt Controller
def login_attempt_list_route():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    login_attempt_list, total_login_attempt = login_attempt_service.get_paginated_login_attempt_list(page, per_page, order)

    return jsonify({
        "login_attempt": [login_attempt.to_dict() for login_attempt in login_attempt_list],
        "total_login_attempt": total_login_attempt,
        "total_pages": (total_login_attempt + per_page - 1) // per_page,
    })


def delete_login_attempt_route(login_attempt_id):
    success = login_attempt_service.delete_login_attempt(login_attempt_id)
    if success:
        return jsonify({"message": "Login Attempt deleted successfully"}), 200
    else:
        return jsonify({"message": "Login Attempt not found"}), 404