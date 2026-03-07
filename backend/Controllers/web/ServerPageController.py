from flask import flash, redirect, render_template, request, session, url_for
import os

from backend.Repositories.ServerChannelRepository import ServerChannelRepository
from backend.Repositories.ServerFileRepository import ServerFileRepository
from backend.Repositories.ServerMessageRepository import ServerMessageRepository
from backend.Repositories.ServerUserRepository import ServerUserRepository
from backend.Services.ServerCommunityService import ServerCommunityService
from backend.configurations import (
    SERVER_APP_PAGE,
    SERVER_ENTRY_PAGE,
    SERVER_FORGOT_PASSWORD_PAGE,
    SERVER_LOGIN_PAGE,
    SERVER_REGISTER_PAGE,
    SERVER_SETTINGS_PAGE,
)


server_community_service = ServerCommunityService(
    user_repository=ServerUserRepository(),
    channel_repository=ServerChannelRepository(),
    message_repository=ServerMessageRepository(),
    file_repository=ServerFileRepository(),
)


def _server_user_id():
    return str(session.get("server_user_id") or "").strip()


def _set_server_session(user_payload: dict):
    session["server_user_id"] = user_payload.get("id")
    session["server_username"] = user_payload.get("username")
    session["server_name"] = user_payload.get("name")
    session["server_account_type"] = user_payload.get("account_type")
    session["server_profile_image"] = user_payload.get("profile_image")
    if user_payload.get("id"):
        server_community_service.set_user_online_status(str(user_payload.get("id")), True)


def _clear_server_session():
    user_id = str(session.get("server_user_id") or "").strip()
    if user_id:
        server_community_service.set_user_online_status(user_id, False)
    for key in (
        "server_user_id",
        "server_username",
        "server_name",
        "server_account_type",
        "server_profile_image",
    ):
        session.pop(key, None)


def _firebase_client_config():
    config = {
        "apiKey": str(os.getenv("FIREBASE_API_KEY") or "").strip(),
        "authDomain": str(os.getenv("FIREBASE_AUTH_DOMAIN") or "").strip(),
        "projectId": str(os.getenv("FIREBASE_PROJECT_ID") or "").strip(),
        "storageBucket": str(os.getenv("FIREBASE_STORAGE_BUCKET") or "").strip(),
        "messagingSenderId": str(os.getenv("FIREBASE_MESSAGING_SENDER_ID") or "").strip(),
        "appId": str(os.getenv("FIREBASE_APP_ID") or "").strip(),
    }

    if not (config["apiKey"] and config["authDomain"] and config["projectId"] and config["appId"]):
        return None
    return config


def server_entry_route():
    server_community_service.seed_defaults()
    if _server_user_id():
        return redirect(url_for("pages.server_app"))
    return render_template(SERVER_ENTRY_PAGE, title="Server Community")


def server_login_route():
    server_community_service.seed_defaults()
    if _server_user_id():
        return redirect(url_for("pages.server_app"))

    if request.method == "POST":
        login_value = str(request.form.get("login") or "").strip()
        password = str(request.form.get("password") or "")
        if not login_value or not password:
            flash("Username/email and password are required.", "warning")
            return render_template(
                SERVER_LOGIN_PAGE,
                title="Server Login",
                firebase_client_config=_firebase_client_config(),
            )

        user_payload, error_message = server_community_service.authenticate(login_value, password)
        if error_message:
            flash(error_message, "danger")
            return render_template(
                SERVER_LOGIN_PAGE,
                title="Server Login",
                firebase_client_config=_firebase_client_config(),
            )

        _set_server_session(user_payload)
        flash("Welcome to Server Community.", "success")
        return redirect(url_for("pages.server_app"))

    return render_template(
        SERVER_LOGIN_PAGE,
        title="Server Login",
        firebase_client_config=_firebase_client_config(),
    )


def server_register_route():
    server_community_service.seed_defaults()
    if _server_user_id():
        return redirect(url_for("pages.server_app"))

    if request.method == "POST":
        payload = {
            "name": request.form.get("name"),
            "birthdate": request.form.get("birthdate"),
            "place": request.form.get("place"),
            "gender": request.form.get("gender"),
            "username": request.form.get("username"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
        }
        confirm_password = str(request.form.get("confirm_password") or "").strip()

        if str(payload.get("password") or "") != confirm_password:
            flash("Password and confirm password do not match.", "danger")
            return render_template(
                SERVER_REGISTER_PAGE,
                title="Create Server Account",
                firebase_client_config=_firebase_client_config(),
            )

        try:
            server_community_service.register_account(payload)
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("pages.server_login"))
        except Exception as exc:
            flash(str(exc), "danger")

    return render_template(
        SERVER_REGISTER_PAGE,
        title="Create Server Account",
        firebase_client_config=_firebase_client_config(),
    )


def server_forgot_password_route():
    if request.method == "POST":
        action = str(request.form.get("action") or "request_otp").strip().lower()
        login_value = str(request.form.get("login") or "").strip()
        if action == "request_otp":
            try:
                result = server_community_service.request_password_reset_otp(login_value)
                masked_email = str(result.get("masked_email") or "").strip()
                if masked_email:
                    flash(f"OTP sent to {masked_email}.", "success")
                else:
                    flash(result.get("message") or "Sorry, this account cannot exist.", "info")
            except Exception as exc:
                flash(str(exc), "danger")
            return redirect(url_for("pages.server_forgot_password"))

        otp_code = str(request.form.get("otp_code") or "").strip()
        new_password = str(request.form.get("new_password") or "").strip()
        confirm_password = str(request.form.get("confirm_password") or "").strip()
        if new_password != confirm_password:
            flash("Password and confirm password do not match.", "danger")
            return redirect(url_for("pages.server_forgot_password"))

        try:
            server_community_service.reset_password_with_otp(
                login_value=login_value,
                otp_code=otp_code,
                new_password=new_password,
            )
            flash("Password reset successful. You can now login.", "success")
            return redirect(url_for("pages.server_login"))
        except Exception as exc:
            flash(str(exc), "danger")
        return redirect(url_for("pages.server_forgot_password"))

    return render_template(
        SERVER_FORGOT_PASSWORD_PAGE,
        title="Forgot Password",
        firebase_client_config=_firebase_client_config(),
    )


def server_app_route():
    user_document = server_community_service.get_user_document_by_id(_server_user_id())
    if not user_document:
        _clear_server_session()
        return redirect(url_for("pages.server_login"))
    server_community_service.touch_user_activity(str(user_document.get("_id")))
    user_document = server_community_service.get_user_document_by_id(str(user_document.get("_id")))

    channels = server_community_service.list_channels_for_user(user_document)
    active_channel_id = str(request.args.get("channel_id") or "")
    if not active_channel_id and channels:
        active_channel_id = str(channels[0].get("id") or "")

    return render_template(
        SERVER_APP_PAGE,
        title="Server Community",
        server_user=server_community_service.serialize_user(user_document),
        server_channels=channels,
        active_channel_id=active_channel_id,
    )


def server_settings_route():
    user_id = _server_user_id()
    user_document = server_community_service.get_user_document_by_id(user_id)
    if not user_document:
        _clear_server_session()
        return redirect(url_for("pages.server_login"))
    server_community_service.touch_user_activity(str(user_document.get("_id")))
    user_document = server_community_service.get_user_document_by_id(str(user_document.get("_id")))

    if request.method == "POST":
        payload = {
            "name": request.form.get("name"),
            "birthdate": request.form.get("birthdate"),
            "place": request.form.get("place"),
            "gender": request.form.get("gender"),
            "username": request.form.get("username"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
        }
        confirm_password = str(request.form.get("confirm_password") or "").strip()
        password = str(payload.get("password") or "").strip()

        if password and password != confirm_password:
            flash("Password and confirm password do not match.", "danger")
        else:
            try:
                updated_user = server_community_service.update_profile(
                    user_id=user_id,
                    data=payload,
                    profile_image_file=request.files.get("profile_image_file"),
                )
                _set_server_session(updated_user)
                user_document = server_community_service.get_user_document_by_id(user_id)
                flash("Profile updated successfully.", "success")
            except Exception as exc:
                flash(str(exc), "danger")

    return render_template(
        SERVER_SETTINGS_PAGE,
        title="Server Settings",
        server_user=server_community_service.serialize_user(user_document),
    )


def server_logout_route():
    _clear_server_session()
    flash("You have been logged out from Server Community.", "success")
    return redirect(url_for("pages.server_login"))
