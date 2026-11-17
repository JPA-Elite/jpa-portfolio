from flask import request

from app.Repositories.UserDisplayNameRepository import UserDisplayNameRepository
from app.Requests.api.UserDisplayNameRequest import UserDisplayNameRequest
from app.Services.UserDisplayNameService import UserDisplayNameService
from app.core.configurations import HTTPMethod as http, HTTPStatus as status
from app.core.responses import errors_response, json_response, status_response
from app.constants.messages import NAME_CHANGE_LIMIT_ERROR

user_display_name_service = UserDisplayNameService(repository=UserDisplayNameRepository())


def comment_username_route():
    form = UserDisplayNameRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    if request.method == http.GET:
        display_name, remaining_changes = user_display_name_service.get_display_name(data["ip_address"])
        return json_response({
            "display_name": display_name,
            "remaining_changes": remaining_changes,
        })

    display_name, remaining_changes = user_display_name_service.save_display_name(
        data["ip_address"], data["display_name"]
    )
    if display_name is None:
        return errors_response(
            {"_global": NAME_CHANGE_LIMIT_ERROR},
            status.TOO_MANY_REQUESTS,
            remaining_changes=remaining_changes,
        )

    return status_response(
        "success",
        display_name=display_name,
        remaining_changes=remaining_changes,
    )
