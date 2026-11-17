import os

import requests

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"


def _hcaptcha_enabled():
    return os.getenv("HCAPTCHA_ENABLED", "true").lower() not in ("false", "0", "no", "off")


def verify_hcaptcha(token: str, remote_ip: str = None):
    if not _hcaptcha_enabled():
        return True, {"success": True, "bypass": True}

    if not token:
        return False, {"error": "missing-token"}

    data = {
        "secret": os.getenv("HCAPTCHA_SECRET_KEY"),
        "response": token,
    }

    if remote_ip:
        if "," in remote_ip:
            remote_ip = remote_ip.split(",")[0].strip()

        data["remoteip"] = remote_ip

    try:
        r = requests.post(HCAPTCHA_VERIFY_URL, data=data, timeout=5)
        r.raise_for_status()
        res = r.json()
        return bool(res.get("success")), res
    except requests.RequestException as e:
        return False, {"error": "request-failed", "exception": str(e)}
