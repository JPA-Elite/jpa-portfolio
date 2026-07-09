from flask import jsonify, request
from typing import Any, Dict, Optional, Tuple


class BaseRequest:
    def __init__(self):
        self._errors: Dict[str, str] = {}

    def validated(self) -> Tuple[Optional[Dict[str, Any]], Any, int]:
        raise NotImplementedError("Subclasses must implement validated()")

    def _error_response(self, status_code: int = 400):
        return jsonify({"errors": self._errors}), status_code

    def _success_response(self, data: Dict[str, Any]):
        return data, None, 200

    @staticmethod
    def _get_form(key: str, default: Any = "") -> Any:
        value = request.form.get(key, default)
        return value if value is not None else default

    @staticmethod
    def _get_file(key: str):
        return request.files.get(key)

    @staticmethod
    def _get_json(key: str, default: Any = None) -> Any:
        payload = request.get_json(silent=True) or {}
        return payload.get(key, default)

    @staticmethod
    def _get_args(key: str, default: Any = "") -> Any:
        value = request.args.get(key, default)
        return value if value is not None else default

    @staticmethod
    def _get_int(key: str, default: int = 0) -> int:
        value = request.args.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get_form_int(key: str, default: int = 0) -> int:
        value = request.form.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_json_field(raw_value: Any):
        import json
        if raw_value is None:
            return None
        if isinstance(raw_value, (dict, list)):
            return raw_value
        if isinstance(raw_value, str):
            try:
                return json.loads(raw_value)
            except (json.JSONDecodeError, ValueError):
                return raw_value
        return raw_value

    @staticmethod
    def _parse_bool(value: Any, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _require(self, key: str, value: Any, message: str = None) -> bool:
        if value is None or (isinstance(value, str) and not value.strip()):
            self._errors[key] = message or f"The {key} field is required."
            return False
        return True
