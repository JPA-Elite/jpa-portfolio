import ipaddress
import os

from flask import Request, jsonify, request

LOCAL_IPS = {"127.0.0.1", "::1", "localhost"}


def _is_truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _extract_client_ip(req: Request) -> str:
    forwarded = req.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return req.remote_addr or ""


def _is_trusted_ip(client_ip: str, trusted_ips: list[str], trusted_cidrs: list[str]) -> bool:
    if client_ip in LOCAL_IPS:
        return True

    try:
        parsed_ip = ipaddress.ip_address(client_ip)
    except ValueError:
        return False

    if client_ip in trusted_ips:
        return True

    for cidr in trusted_cidrs:
        try:
            if parsed_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue

    return False


def trusted_network_guard():
    """
    Global request gate for trusted networks.

    Behavior:
    - Local/dev (`FLASK_DEBUG=1`): no blocking.
    - Production: blocks requests when `ENFORCE_TRUSTED_NETWORK=true` and
      client IP is not in TRUSTED_IPS or TRUSTED_CIDRS.
    """

    debug_enabled = _is_truthy(os.getenv("FLASK_DEBUG", "0"))
    enforce = _is_truthy(os.getenv("ENFORCE_TRUSTED_NETWORK", "0"))

    if debug_enabled or not enforce:
        return None

    trusted_ips = _parse_csv_env("TRUSTED_IPS")
    trusted_cidrs = _parse_csv_env("TRUSTED_CIDRS")

    client_ip = _extract_client_ip(request)
    if _is_trusted_ip(client_ip, trusted_ips, trusted_cidrs):
        return None

    return jsonify({
        "status": "error",
        "message": "Access denied: untrusted network.",
    }), 403
