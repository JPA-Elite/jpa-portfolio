from functools import wraps
from typing import Any

from bson import ObjectId
from flask import jsonify, request

MAX_INPUT_LENGTH = 5000


def _is_malicious_key(key: str) -> bool:
    return key.startswith("$") or "." in key


def _validate_value(value: Any, path: str = "root"):
    if isinstance(value, dict):
        for k, v in value.items():
            if _is_malicious_key(str(k)):
                raise ValueError(f"Invalid key at {path}.{k}")
            _validate_value(v, f"{path}.{k}")
        return

    if isinstance(value, list):
        for idx, item in enumerate(value):
            _validate_value(item, f"{path}[{idx}]")
        return

    if isinstance(value, str):
        if "\x00" in value:
            raise ValueError(f"Null byte found at {path}")
        if len(value) > MAX_INPUT_LENGTH:
            raise ValueError(f"Input too long at {path}")


def require_safe_input(f):
    """Basic request validation to mitigate common NoSQL/operator injection payloads."""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            _validate_value(request.args.to_dict(flat=False), "query")
            _validate_value(request.form.to_dict(flat=False), "form")

            if request.is_json:
                payload = request.get_json(silent=True)
                if payload is not None:
                    _validate_value(payload, "json")
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

        return f(*args, **kwargs)

    return decorated


def validate_object_id_param(param_name: str):
    """Ensure path parameter is a valid Mongo ObjectId before reaching controllers/services."""

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            value = kwargs.get(param_name)
            if value is None or not ObjectId.is_valid(value):
                return jsonify({"status": "error", "message": f"Invalid {param_name}"}), 400
            return f(*args, **kwargs)

        return wrapped

    return decorator
