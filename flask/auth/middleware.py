# app/middleware.py
from flask import session, redirect, url_for, flash
from functools import wraps
from constants.login_roles import ROLE_ADMIN

def admin_login_required(f):
    """Protect routes to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        role = session.get("role")

        if not user_id:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("pages.admin_login"))

        if role != ROLE_ADMIN:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("pages.admin_login"))

        return f(*args, **kwargs)

    return decorated_function
