from datetime import timedelta
from flask import current_app, flash, redirect, render_template, request, session, url_for
from config import (
    ADMIN_CHAT_PAGE,
    ADMIN_DASHBOARD_PAGE,
    ADMIN_LOGIN_PAGE,
    ADMIN_MUSIC_PAGE,
    ADMIN_PROJECT_PAGE,
    ADMIN_SETTINGS_PAGE,
    ADMIN_VIDEO_PAGE,
)
from config import HTTPMethod as http
from constants.login_roles import ROLE_ADMIN

# ************************** PAGES ********************************
def admin_login_route():
    # If already logged in as admin, redirect to dashboard
    if "user_id" in session and session.get("role") == ROLE_ADMIN:
        return redirect(url_for("pages.admin_dashboard"))

    if request.method == http.POST:
        username = request.form.get("username")
        password = request.form.get("password")
        remember = request.form.get("remember")

        # Dummy admin (replace with DB later)
        if username == "admin" and password == "1234":
            session["user_id"] = username
            session["role"] = ROLE_ADMIN

            # ✅ Set session lifetime if "remember me" is checked
            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False

            flash("Welcome back, Admin!", "success")
            return redirect(url_for("pages.admin_dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template(ADMIN_LOGIN_PAGE)

def admin_logout_route():
    """Logout admin and clear session."""
    session.clear()  # Remove all session data
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("pages.admin_login"))

def admin_dashboard_route():
    return render_template(ADMIN_DASHBOARD_PAGE, title="Admin Dashboard")

def admin_chat_route():
    return render_template(ADMIN_CHAT_PAGE, title="Admin Chat")

def admin_video_route():
    return render_template(ADMIN_VIDEO_PAGE, title="Admin Video")

def admin_music_route():
    return render_template(ADMIN_MUSIC_PAGE, title="Admin Music")

def admin_project_route():
    return render_template(ADMIN_PROJECT_PAGE, title="Admin Project")

def admin_settings_route():
    return render_template(ADMIN_SETTINGS_PAGE, title="Admin Settings")