import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from flask import request, session
from app.extensions import cache
from .ddos_guard import get_request_ip


def _safe_int_env(name: str, default: int):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _safe_bool_env(name: str, default: bool):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _hash_key(value: str):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _cache_get_int(key: str):
    value = cache.get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _cache_set_int(key: str, value: int, timeout: int):
    cache.set(key, int(value), timeout=max(1, timeout))


def _cache_get_lock_seconds(key: str):
    expires_at = _cache_get_int(key)
    if not expires_at:
        return 0
    return max(0, expires_at - int(time.time()))


def _set_lock(key: str, seconds: int):
    seconds = max(1, seconds)
    expires_at = int(time.time()) + seconds
    cache.set(key, expires_at, timeout=seconds + 5)


@dataclass(frozen=True)
class AdminLoginGateResult:
    allowed: bool
    message: str = ""
    retry_after_seconds: int = 0

class AdminLoginSecurity:
    SESSION_NONCE_KEY = "_admin_login_nonce"
    SESSION_ISSUED_AT_KEY = "_admin_login_form_issued_at"
    NONCE_FIELD = "_admin_login_nonce"
    HONEYPOT_FIELD = "company_website"

    def __init__(self):
        self.enabled = _safe_bool_env("ADMIN_LOGIN_GUARD_ENABLED", True)
        self.min_form_age_seconds = _safe_int_env("ADMIN_LOGIN_MIN_FORM_AGE_SECONDS", 1)
        self.max_form_age_seconds = _safe_int_env("ADMIN_LOGIN_MAX_FORM_AGE_SECONDS", 1800)
        self.window_seconds = _safe_int_env("ADMIN_LOGIN_FAIL_WINDOW_SECONDS", 900)
        self.max_failures_per_ip = _safe_int_env("ADMIN_LOGIN_MAX_FAILURES_PER_IP", 8)
        self.max_failures_per_username = _safe_int_env("ADMIN_LOGIN_MAX_FAILURES_PER_USERNAME", 10)
        self.max_failures_per_ip_username = _safe_int_env("ADMIN_LOGIN_MAX_FAILURES_PER_IP_USERNAME", 5)
        self.cooldown_base_seconds = _safe_int_env("ADMIN_LOGIN_COOLDOWN_BASE_SECONDS", 2)
        self.cooldown_max_seconds = _safe_int_env("ADMIN_LOGIN_COOLDOWN_MAX_SECONDS", 60)
        self.lock_seconds_ip = _safe_int_env("ADMIN_LOGIN_LOCK_SECONDS_IP", 1800)  # 30 min
        self.lock_seconds_username = _safe_int_env("ADMIN_LOGIN_LOCK_SECONDS_USERNAME", 3600)  # 60 min
        self.lock_seconds_ip_username = _safe_int_env("ADMIN_LOGIN_LOCK_SECONDS_IP_USERNAME", 3600)

    def _username_key(self, username: str):
        return _hash_key((username or "").strip().lower() or "unknown")

    def _ip_key(self):
        return _hash_key(get_request_ip())

    def _ip_user_key(self, username: str):
        return _hash_key(f"{get_request_ip()}|{(username or '').strip().lower()}")

    def _counter_key(self, scope: str, identity_key: str):
        return f"admin_login:fail:{scope}:{identity_key}"

    def _lock_key(self, scope: str, identity_key: str):
        return f"admin_login:lock:{scope}:{identity_key}"

    def _cooldown_key(self, identity_key: str):
        return f"admin_login:cooldown:{identity_key}"

    def issue_form_challenge(self):
        nonce = secrets.token_urlsafe(24)
        issued_at = int(time.time())
        session[self.SESSION_NONCE_KEY] = nonce
        session[self.SESSION_ISSUED_AT_KEY] = issued_at
        return {
            "admin_login_nonce": nonce,
            "admin_login_honeypot_field": self.HONEYPOT_FIELD,
        }

    def validate_form_submission(self):
        if not self.enabled:
            return AdminLoginGateResult(True)

        honeypot_value = (request.form.get(self.HONEYPOT_FIELD) or "").strip()
        if honeypot_value:
            return AdminLoginGateResult(False, "Invalid login request.")

        provided_nonce = request.form.get(self.NONCE_FIELD, "")
        expected_nonce = session.get(self.SESSION_NONCE_KEY, "")
        issued_at = session.get(self.SESSION_ISSUED_AT_KEY)
        session.pop(self.SESSION_NONCE_KEY, None)
        session.pop(self.SESSION_ISSUED_AT_KEY, None)

        if not provided_nonce or not expected_nonce:
            return AdminLoginGateResult(False, "Login form expired. Please try again.")

        if not hmac.compare_digest(str(provided_nonce), str(expected_nonce)):
            return AdminLoginGateResult(False, "Invalid login request.")

        try:
            issued_at_int = int(issued_at)
        except (TypeError, ValueError):
            issued_at_int = 0

        age_seconds = int(time.time()) - issued_at_int
        if age_seconds < self.min_form_age_seconds:
            return AdminLoginGateResult(False, "Please wait a moment before submitting.")

        if age_seconds > self.max_form_age_seconds:
            return AdminLoginGateResult(False, "Login form expired. Please try again.")

        return AdminLoginGateResult(True)

    def check_before_auth(self, username: str):
        if not self.enabled:
            return AdminLoginGateResult(True)

        username_key = self._username_key(username)
        ip_key = self._ip_key()
        ip_user_key = self._ip_user_key(username)

        lock_checks = (
            self._lock_key("ip_user", ip_user_key),
            self._lock_key("ip", ip_key),
            self._lock_key("username", username_key),
            self._cooldown_key(ip_user_key),
        )

        max_retry = 0
        for key in lock_checks:
            retry_after = _cache_get_lock_seconds(key)
            if retry_after > 0:
                max_retry = max(max_retry, retry_after)

        if max_retry > 0:
            return AdminLoginGateResult(
                False,
                f"Too many login attempts. Try again in {max_retry} second(s).",
                retry_after_seconds=max_retry,
            )

        return AdminLoginGateResult(True)

    def record_failure(self, username: str):
        if not self.enabled:
            return

        username_key = self._username_key(username)
        ip_key = self._ip_key()
        ip_user_key = self._ip_user_key(username)
        ip_count = self._increment_counter("ip", ip_key)
        user_count = self._increment_counter("username", username_key)
        ip_user_count = self._increment_counter("ip_user", ip_user_key)

        cooldown_delay = min(
            self.cooldown_max_seconds,
            max(0, self.cooldown_base_seconds * (2 ** max(0, ip_user_count - 1))),
        )
        if cooldown_delay > 0:
            _set_lock(self._cooldown_key(ip_user_key), cooldown_delay)

        if ip_count >= self.max_failures_per_ip:
            _set_lock(self._lock_key("ip", ip_key), self.lock_seconds_ip)

        if user_count >= self.max_failures_per_username:
            _set_lock(self._lock_key("username", username_key), self.lock_seconds_username)

        if ip_user_count >= self.max_failures_per_ip_username:
            _set_lock(self._lock_key("ip_user", ip_user_key), self.lock_seconds_ip_username)

    def record_success(self, username: str) -> None:
        if not self.enabled:
            return

        username_key = self._username_key(username)
        ip_key = self._ip_key()
        ip_user_key = self._ip_user_key(username)

        for key in (
            self._counter_key("ip_user", ip_user_key),
            self._cooldown_key(ip_user_key),
            self._lock_key("ip_user", ip_user_key),
        ):
            cache.delete(key)

        self._decay_counter(self._counter_key("ip", ip_key))
        self._decay_counter(self._counter_key("username", username_key))

    def _increment_counter(self, scope: str, identity_key: str):
        cache_key = self._counter_key(scope, identity_key)
        current = _cache_get_int(cache_key) + 1
        _cache_set_int(cache_key, current, self.window_seconds)
        return current

    def _decay_counter(self, cache_key: str):
        current = _cache_get_int(cache_key)
        if current <= 1:
            cache.delete(cache_key)
            return
        _cache_set_int(cache_key, max(0, current // 2), self.window_seconds)
