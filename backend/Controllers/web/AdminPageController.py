from datetime import timedelta
from flask import current_app, flash, redirect, render_template, request, session, url_for
from backend.configurations import (
    ADMIN_DASHBOARD_PAGE,
    ADMIN_GALLERY_PAGE,
    ADMIN_LOGIN_ATTEMPTS_PAGE,
    ADMIN_LOGIN_PAGE,
    ADMIN_MUSIC_PAGE,
    ADMIN_KEY_PROJECTS_PAGE,
    ADMIN_SETTINGS_PAGE,
    ADMIN_VIDEO_PAGE,
)
from backend.configurations import HTTPMethod as http
from backend.constants.login_roles import ROLE_ADMIN
from backend.Services.AuthService import AuthService
from backend.Repositories.AuthRepository import AuthRepository
from backend.Repositories.LoginAttemptRepository import LoginAttemptRepository
from backend.constants.messages import CAPTCHA_VERIFICATION_ERROR, LOGOUT_SUCCESS_MSG, WELCOME_ADMIN_MSG
from backend.utils import verify_hcaptcha
from backend.forms.LoginForm import LoginForm

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

    form = LoginForm()
    if form.validate_on_submit():
        # First check captcha
        hcaptcha_token = request.form.get("h-captcha-response", None)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ok, details = verify_hcaptcha(hcaptcha_token, remote_ip=client_ip)
        if not ok:
            current_app.logger.info("hCaptcha failed: %s", details)
            flash(f"{CAPTCHA_VERIFICATION_ERROR} {details}", "warning")
            return render_template(ADMIN_LOGIN_PAGE, form=form)

        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        user, message, locked = auth_service.authenticate_admin(username, password)

        if locked:
            flash(message, "danger")
            return render_template(ADMIN_LOGIN_PAGE, form=form)

        if user:
            session['username'] = username
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]

            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False

            flash(WELCOME_ADMIN_MSG, "success")
            return redirect(url_for("pages.admin_dashboard"))

        # Invalid login
        flash(message, "warning")

    return render_template(ADMIN_LOGIN_PAGE, form=form)

def admin_logout_route():
    """Logout admin and clear session."""
    session.clear()  # Remove all session data
    flash(LOGOUT_SUCCESS_MSG, "success")
    return redirect(url_for("pages.admin_login"))

def admin_dashboard_route():
    return render_template(ADMIN_DASHBOARD_PAGE, title="Admin Dashboard")

def admin_gallery_route():
    return render_template(ADMIN_GALLERY_PAGE, title="Admin Gallery")

def admin_video_route():
    return render_template(ADMIN_VIDEO_PAGE, title="Admin Video")

def admin_music_route():
    return render_template(ADMIN_MUSIC_PAGE, title="Admin Music")

def admin_key_projects_route():
    return render_template(ADMIN_KEY_PROJECTS_PAGE, title="Admin Key Projects")

def admin_settings_route():
    return render_template(ADMIN_SETTINGS_PAGE, title="Admin Settings")

def admin_login_attempts_route():
    return render_template(ADMIN_LOGIN_ATTEMPTS_PAGE, title="Login Attempts")
