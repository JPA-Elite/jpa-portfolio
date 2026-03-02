# app/middleware.py
from flask import session, redirect, url_for, flash
from functools import wraps
from constants.login_roles import ROLE_ADMIN
from constants.messages import LOGIN_ACCESS_ERROR, PERMISSION_ACCESS_PAGE_ERROR

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
