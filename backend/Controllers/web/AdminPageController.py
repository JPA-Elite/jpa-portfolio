from datetime import timedelta
from flask import current_app, flash, make_response, redirect, render_template, request, session, url_for
from backend.configurations import (
    ADMIN_DASHBOARD_PAGE,
    ADMIN_GALLERY_PAGE,
    ADMIN_LOGIN_ATTEMPTS_PAGE,
    ADMIN_LOGIN_PAGE,
    ADMIN_MUSIC_PAGE,
    ADMIN_KEY_PROJECTS_PAGE,
    ADMIN_COMPANY_ROADMAPS_PAGE,
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
from backend.security import AdminLoginSecurity, get_request_ip

# Initialize Services
auth_service = AuthService(
    repository=AuthRepository(),
    attempt_repository=LoginAttemptRepository()
)
admin_login_security = AdminLoginSecurity()


def _render_admin_login(form, errors=None, status_code=200):
    """Render admin login with one-time anti-automation fields and no-store headers."""
    security_context = admin_login_security.issue_form_challenge()
    response = make_response(
        render_template(ADMIN_LOGIN_PAGE, form=form, errors=errors or {}, **security_context),
        status_code,
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ************************** PAGES ********************************
def admin_login_route():
    # If already logged in as admin, redirect to dashboard
    if "user_id" in session and session.get("role") == ROLE_ADMIN:
        return redirect(url_for("pages.admin_dashboard"))

    form = LoginForm()
    if request.method == http.POST and not form.validate_on_submit():
        # Includes invalid CSRF/malformed submissions; count it as suspicious login traffic.
        admin_login_security.record_failure(request.form.get("username", ""))
        flash("Invalid login request. Please try again.", "warning")
        return _render_admin_login(form, status_code=400)

    if form.validate_on_submit():
        username = (form.username.data or "").strip()
        password = form.password.data or ""

        # Manual field-level validation
        errors = {}
        if not username:
            errors["username"] = "Username is required."
        if not password:
            errors["password"] = "Password is required."
        if errors:
            return _render_admin_login(form, errors=errors, status_code=400)

        form_gate = admin_login_security.validate_form_submission()
        if not form_gate.allowed:
            admin_login_security.record_failure(username)
            flash(form_gate.message, "warning")
            return _render_admin_login(form, status_code=400)

        pre_auth_gate = admin_login_security.check_before_auth(username)
        if not pre_auth_gate.allowed:
            flash(pre_auth_gate.message, "danger")
            return _render_admin_login(form, status_code=429)

        # First check captcha
        hcaptcha_token = request.form.get("h-captcha-response", None)
        client_ip = get_request_ip()
        ok, details = verify_hcaptcha(hcaptcha_token, remote_ip=client_ip)
        if not ok:
            current_app.logger.info("hCaptcha failed: %s", details)
            admin_login_security.record_failure(username)
            flash(CAPTCHA_VERIFICATION_ERROR, "warning")
            return _render_admin_login(form, status_code=400)

        password = password  # already extracted above
        remember = form.remember.data

        user, message, locked = auth_service.authenticate_admin(username, password)

        if locked:
            admin_login_security.record_failure(username)
            flash(message, "danger")
            return _render_admin_login(form, status_code=429)

        if user:
            # Clear any pre-login session data to reduce session fixation risk.
            session.clear()
            session['username'] = user.get("username") or username
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]
            session["profile_image"] = user.get("profile_image")
            admin_login_security.record_success(username)

            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False

            flash(WELCOME_ADMIN_MSG, "success")
            return redirect(url_for("pages.admin_dashboard"))

        # Invalid login
        admin_login_security.record_failure(username)
        flash("Invalid username or password.", "warning")

    return _render_admin_login(form)

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

def admin_company_roadmaps_route():
    return render_template(ADMIN_COMPANY_ROADMAPS_PAGE, title="Admin Company Roadmaps")

def admin_settings_route():
    return render_template(ADMIN_SETTINGS_PAGE, title="Admin Settings")

def admin_login_attempts_route():
    return render_template(ADMIN_LOGIN_ATTEMPTS_PAGE, title="Login Attempts")
