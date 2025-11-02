from datetime import timedelta
from flask import current_app, flash, redirect, render_template, request, session, url_for
from config import (
    ADMIN_DASHBOARD_PAGE,
    ADMIN_GALLERY_PAGE,
    ADMIN_LOGIN_ATTEMPTS_PAGE,
    ADMIN_LOGIN_PAGE,
    ADMIN_MUSIC_PAGE,
    ADMIN_SETTINGS_PAGE,
    ADMIN_VIDEO_PAGE,
)
from config import HTTPMethod as http
from constants.login_roles import ROLE_ADMIN
from Services.AuthService import AuthService
from Repositories.AuthRepository import AuthRepository
from Repositories.LoginAttemptRepository import LoginAttemptRepository

# Initialize Services
auth_service = AuthService(
    repository=AuthRepository(),
    attempt_repository=LoginAttemptRepository()
)

# ************************** PAGES ********************************
def admin_login_route():
    # If already logged in as admin, redirect to dashboard
    if "user_id" in session and session.get("role") == ROLE_ADMIN:
        return redirect(url_for("pages.admin_dashboard"))

    if request.method == http.POST:
        username = request.form.get("username")
        password = request.form.get("password")
        remember = request.form.get("remember")

        user, message, locked = auth_service.authenticate_admin(username, password)

        if locked:
            flash(message, "danger")
            return render_template(ADMIN_LOGIN_PAGE)

        if user:
            session['username'] = username
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]

            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False

            flash("Welcome back, Admin!", "success")
            return redirect(url_for("pages.admin_dashboard"))

        # Invalid login
        flash(message, "warning")

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

def admin_login_attempts_route():
    return render_template(ADMIN_LOGIN_ATTEMPTS_PAGE, title="Login Attempts")