from flask import jsonify, request

from app.Repositories.UserDisplayNameRepository import UserDisplayNameRepository
from app.Requests.api.UserDisplayNameRequest import UserDisplayNameRequest
from app.Services.UserDisplayNameService import UserDisplayNameService
from app.configurations import HTTPMethod as http
from app.constants.messages import NAME_CHANGE_LIMIT_ERROR

user_display_name_service = UserDisplayNameService(repository=UserDisplayNameRepository())


def comment_username_route():
    form = UserDisplayNameRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    if request.method == http.GET:
        display_name, remaining_changes = user_display_name_service.get_display_name(data["ip_address"])
        return jsonify({
            "display_name": display_name,
            "remaining_changes": remaining_changes,
        })

    display_name, remaining_changes = user_display_name_service.save_display_name(
        data["ip_address"], data["display_name"]
    )
    if display_name is None:
        return jsonify({
            "errors": {"_global": NAME_CHANGE_LIMIT_ERROR},
            "remaining_changes": remaining_changes,
        }), 429

    return jsonify({
        "status": "success",
        "display_name": display_name,
        "remaining_changes": remaining_changes,
    })
