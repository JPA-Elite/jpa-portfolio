import hashlib
import ipaddress
import os
import time
from dataclasses import dataclass
from typing import Optional, Sequence
from flask import jsonify, request
from app.extensions import cache


def _env_flag(name: str, default: bool):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}

def _safe_int_env(name: str, default: int):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _normalize_ip(candidate: Optional[str]):
    if not candidate:
        return None

    value = candidate.strip()
    if not value:
        return None

    if value.startswith("[") and "]" in value:
        value = value[1:value.index("]")]

    if value.count(":") == 1 and "." in value:
        host, _, _port = value.partition(":")
        value = host.strip()

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def get_request_ip():
    for header_name in ("CF-Connecting-IP", "True-Client-IP", "X-Real-IP"):
        normalized = _normalize_ip(request.headers.get(header_name))
        if normalized:
            return normalized

    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        for part in forwarded_for.split(","):
            normalized = _normalize_ip(part)
            if normalized:
                return normalized

    return _normalize_ip(request.remote_addr) or "0.0.0.0"

def _request_key():
    ip_address = get_request_ip()
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()[:24]

@dataclass(frozen=True)
class RateLimitRule:
    name: str
    limit: int
    window_seconds: int
    path_prefixes: Sequence[str]
    methods: Optional[Sequence[str]] = None

    def matches(self) -> bool:
        if self.methods and request.method.upper() not in {m.upper() for m in self.methods}:
            return False

        path = request.path or "/"
        return any(path.startswith(prefix) for prefix in self.path_prefixes)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    reset_seconds: int
    count: int

class SimpleRateLimiter:
    def consume(self, rule: RateLimitRule, subject_key: str):
        now = int(time.time())
        bucket = now // rule.window_seconds
        cache_key = f"rl:{rule.name}:{bucket}:{subject_key}"
        expires_in = max(1, rule.window_seconds - (now % rule.window_seconds))

        current = cache.get(cache_key)
        try:
            count = int(current or 0)
        except (TypeError, ValueError):
            count = 0

        count += 1
        cache.set(cache_key, count, timeout=rule.window_seconds + 2)

        remaining = max(0, rule.limit - count)
        allowed = count <= rule.limit
        retry_after = expires_in if not allowed else 0

        return RateLimitResult(
            allowed=allowed,
            limit=rule.limit,
            remaining=remaining,
            retry_after=retry_after,
            reset_seconds=expires_in,
            count=count,
        )


def _is_exempt_request():
    if request.method.upper() == "OPTIONS":
        return True

    path = request.path or "/"
    if path.startswith("/static/"):
        return True

    if path in {"/favicon.ico"}:
        return True

    return False


def _default_rules():
    return (
        RateLimitRule(
            name="global_burst",
            limit=_safe_int_env("DDOS_GUARD_GLOBAL_BURST_LIMIT", 80),
            window_seconds=_safe_int_env("DDOS_GUARD_GLOBAL_BURST_WINDOW", 10),
            path_prefixes=("/",),
        ),
        RateLimitRule(
            name="global_sustained",
            limit=_safe_int_env("DDOS_GUARD_GLOBAL_SUSTAINED_LIMIT", 900),
            window_seconds=_safe_int_env("DDOS_GUARD_GLOBAL_SUSTAINED_WINDOW", 300),
            path_prefixes=("/",),
        ),
        RateLimitRule(
            name="media_proxy_burst",
            limit=_safe_int_env("DDOS_GUARD_MEDIA_BURST_LIMIT", 12),
            window_seconds=_safe_int_env("DDOS_GUARD_MEDIA_BURST_WINDOW", 10),
            path_prefixes=("/api/proxy-audio", "/api/download_song"),
            methods=("GET",),
        ),
        RateLimitRule(
            name="media_proxy_sustained",
            limit=_safe_int_env("DDOS_GUARD_MEDIA_SUSTAINED_LIMIT", 120),
            window_seconds=_safe_int_env("DDOS_GUARD_MEDIA_SUSTAINED_WINDOW", 300),
            path_prefixes=("/api/proxy-audio", "/api/download_song"),
            methods=("GET",),
        ),
        RateLimitRule(
            name="engagement_write_burst",
            limit=_safe_int_env("DDOS_GUARD_ENGAGEMENT_BURST_LIMIT", 10),
            window_seconds=_safe_int_env("DDOS_GUARD_ENGAGEMENT_BURST_WINDOW", 10),
            path_prefixes=(
                "/api/gallery-like",
                "/api/vlog-like",
                "/api/gallery-comments",
                "/api/vlog-comments",
            ),
            methods=("POST",),
        ),
        RateLimitRule(
            name="engagement_write_sustained",
            limit=_safe_int_env("DDOS_GUARD_ENGAGEMENT_SUSTAINED_LIMIT", 120),
            window_seconds=_safe_int_env("DDOS_GUARD_ENGAGEMENT_SUSTAINED_WINDOW", 300),
            path_prefixes=(
                "/api/gallery-like",
                "/api/vlog-like",
                "/api/gallery-comments",
                "/api/vlog-comments",
            ),
            methods=("POST",),
        ),
        RateLimitRule(
            name="admin_login",
            limit=_safe_int_env("DDOS_GUARD_ADMIN_LOGIN_LIMIT", 8),
            window_seconds=_safe_int_env("DDOS_GUARD_ADMIN_LOGIN_WINDOW", 300),
            path_prefixes=("/admin/login",),
            methods=("POST",),
        ),
    )

def _is_api_request():
    path = request.path or "/"
    return path.startswith("/api/") or path.startswith("/admin/api/")

def _build_429_response(limit_name: str, result: RateLimitResult):
    message = "Too many requests. Please retry shortly."

    if _is_api_request():
        response = jsonify(
            {
                "error": "rate_limit_exceeded",
                "message": message,
                "limit": limit_name,
                "retry_after_seconds": result.retry_after,
            }
        )
    else:
        response = jsonify(
            {
                "error": "rate_limit_exceeded",
                "message": message,
                "retry_after_seconds": result.retry_after,
            }
        )
        response.headers["Content-Type"] = "application/json; charset=utf-8"

    response.status_code = 429
    response.headers["Retry-After"] = str(result.retry_after or 1)
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(result.reset_seconds)
    return response


def init_ddos_guard(app):
    if not _env_flag("DDOS_GUARD_ENABLED", True):
        app.logger.info("DDoS guard disabled via DDOS_GUARD_ENABLED")
        return

    app.config.setdefault(
        "MAX_CONTENT_LENGTH",
        _safe_int_env("MAX_CONTENT_LENGTH_BYTES", 300 * 1024 * 1024),
    )

    limiter = SimpleRateLimiter()
    rules = tuple(_default_rules())

    @app.before_request
    def ddos_guard_before_request():
        if _is_exempt_request():
            return None

        subject_key = _request_key()

        for rule in rules:
            if not rule.matches():
                continue

            result = limiter.consume(rule, subject_key)
            if not result.allowed:
                return _build_429_response(rule.name, result)

        return None

    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        if request.path in {"/admin/settings", "/admin/face-recognition", "/admin/login"}:
            response.headers["Permissions-Policy"] = "camera=(self)"
        else:
            response.headers.setdefault(
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=()",
            )
        return response
