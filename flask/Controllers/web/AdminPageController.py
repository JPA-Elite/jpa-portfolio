from datetime import timedelta, datetime
from flask import current_app, flash, redirect, render_template, request, session, url_for
from config import (
    ADMIN_DASHBOARD_PAGE,
    ADMIN_GALLERY_PAGE,
    ADMIN_LOGIN_PAGE,
    ADMIN_MUSIC_PAGE,
    ADMIN_SETTINGS_PAGE,
    ADMIN_VIDEO_PAGE,
)
from config import HTTPMethod as http
from constants.login_roles import ROLE_ADMIN
from Services.AuthService import AuthService
from Repositories.AuthRepository import AuthRepository

# Initialize Services
auth_service = AuthService(repository=AuthRepository())

MAX_ATTEMPTS = 3
LOCKOUT_TIME = timedelta(hours=1)

# ************************** PAGES ********************************
def admin_login_route():
    # If already logged in as admin, redirect to dashboard
    if "user_id" in session and session.get("role") == ROLE_ADMIN:
        return redirect(url_for("pages.admin_dashboard"))

    # Initialize attempt tracking for this user
    if "login_attempts" not in session:
        session["login_attempts"] = 0
        session["lockout_until"] = None

    lockout_until = session.get("lockout_until")
    if lockout_until and datetime.utcnow() < datetime.fromisoformat(lockout_until):
        remaining = datetime.fromisoformat(lockout_until) - datetime.utcnow()
        flash(f"Too many failed attempts. Please wait {int(remaining.total_seconds() // 60)} minutes before trying again.", "danger")
        return render_template(ADMIN_LOGIN_PAGE)

    if request.method == http.POST:
        username = request.form.get("username")
        password = request.form.get("password")
        remember = request.form.get("remember")

        user = auth_service.authenticate_admin(username, password)
        if user:
            session["login_attempts"] = 0
            session["lockout_until"] = None
            session['username'] = username
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]

            # ✅ Set session lifetime if "remember me" is checked
            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False

            flash("Welcome back, Admin!", "success")
            return redirect(url_for("pages.admin_dashboard"))
        else:
            session["login_attempts"] += 1
            if session["login_attempts"] >= MAX_ATTEMPTS:
                lockout_until_time = datetime.utcnow() + LOCKOUT_TIME
                session["lockout_until"] = lockout_until_time.isoformat()
                flash("Too many failed attempts. Please wait 1 hour before logging in again.", "danger")
            else:
                remaining = MAX_ATTEMPTS - session["login_attempts"]
                flash(f"Invalid username or password. {remaining} attempt(s) left.", "warning")

    return render_template(ADMIN_LOGIN_PAGE)

def admin_logout_route():
    """Logout admin and clear session."""
    session.clear()  # Remove all session data
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("pages.admin_login"))

def admin_dashboard_route():
    return render_template(ADMIN_DASHBOARD_PAGE, title="Admin Dashboard")

def admin_gallery_route():
    return render_template(ADMIN_GALLERY_PAGE, title="Admin Gallery")

def admin_video_route():
    return render_template(ADMIN_VIDEO_PAGE, title="Admin Video")

def admin_music_route():
    return render_template(ADMIN_MUSIC_PAGE, title="Admin Music")

def admin_settings_route():
    return render_template(ADMIN_SETTINGS_PAGE, title="Admin Settings")