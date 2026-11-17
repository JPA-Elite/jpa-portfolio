from flask import jsonify
from app.core.configurations import HTTPStatus as status


def json_response(payload, status_code=status.OK):
    return jsonify(payload), status_code


def message_response(message, status_code=status.OK, **extra):
    return json_response({"message": message, **extra}, status_code)


def created_response(message, **extra):
    return json_response({"message": message, **extra}, status.CREATED)


def ok_response(message=None, status_code=status.OK, **extra):
    payload = {"ok": True}
    if message is not None:
        payload["message"] = message
    payload.update(extra)
    return json_response(payload, status_code)


def ok_error_response(message, status_code=status.BAD_REQUEST, **extra):
    return json_response({"ok": False, "message": message, **extra}, status_code)


def result_response(result, status_code=status.OK):
    return json_response(
        {
            "ok": result.get("status") == "success",
            "message": result.get("message", ""),
        },
        status_code,
    )


def status_response(state, message=None, status_code=status.OK, **extra):
    payload = {"status": state}
    if message is not None:
        payload["message"] = message
    payload.update(extra)
    return json_response(payload, status_code)


def errors_response(errors, status_code=status.BAD_REQUEST, **extra):
    return json_response({"errors": errors, **extra}, status_code)


def error_message_response(message, status_code=status.BAD_REQUEST, **extra):
    return json_response({"error": message, **extra}, status_code)
