from flask import session, redirect, url_for, flash, request
from functools import wraps
from app.constants.login_roles import ROLE_ADMIN
from app.constants.messages import LOGIN_ACCESS_ERROR, PERMISSION_ACCESS_PAGE_ERROR

FACE_VERIFIED_SESSION_KEY = "face_verified"
FACE_ONLY_ENDPOINT = "pages.admin_face_recognition"


def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        role = session.get("role")

        if not user_id:
            flash(LOGIN_ACCESS_ERROR, "warning")
            return redirect(url_for("pages.admin_login"))

        if role != ROLE_ADMIN:
            flash(PERMISSION_ACCESS_PAGE_ERROR, "danger")
            return redirect(url_for("pages.admin_login"))

        allowed_before_face_verified_paths = {
            "/admin/api/face/register",
            "/admin/api/face/verify",
            "/admin/api/face/records",
            "/admin/api/otp/send",
            "/admin/api/otp/verify",
            "/admin/api/otp/email",
        }
        request_path = request.path or ""

        if (
            not session.get(FACE_VERIFIED_SESSION_KEY)
            and request.endpoint not in {FACE_ONLY_ENDPOINT, "pages.admin_login"}
            and request_path not in allowed_before_face_verified_paths
        ):
            return redirect(url_for("pages.admin_face_recognition"))

        return f(*args, **kwargs)

    return decorated_function
