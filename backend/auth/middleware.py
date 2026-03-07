# app/middleware.py
from flask import jsonify, session, redirect, url_for, flash
from functools import wraps
from backend.constants.login_roles import ROLE_ADMIN
from backend.constants.messages import LOGIN_ACCESS_ERROR, PERMISSION_ACCESS_PAGE_ERROR

def admin_login_required(f):
    """Protect routes to require admin login."""
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

        return f(*args, **kwargs)

    return decorated_function


def server_login_required(f):
    """Protect web routes to require server-community login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("server_user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("pages.server_login"))
        return f(*args, **kwargs)

    return decorated_function


def server_admin_required(f):
    """Protect web routes to require server-community admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("server_user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("pages.server_login"))

        if (session.get("server_account_type") or "").lower() != "admin":
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("pages.server_app"))

        return f(*args, **kwargs)

    return decorated_function


def server_api_login_required(f):
    """Protect API routes to require server-community login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("server_user_id"):
            return jsonify({"message": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated_function


def server_api_admin_required(f):
    """Protect API routes to require server-community admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("server_user_id"):
            return jsonify({"message": "Unauthorized"}), 401
        if (session.get("server_account_type") or "").lower() != "admin":
            return jsonify({"message": "Forbidden"}), 403
        return f(*args, **kwargs)

    return decorated_function
