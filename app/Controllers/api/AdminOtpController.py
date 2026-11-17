from flask import request, session
from app.Services.OtpService import OtpService
from app.Requests.api.AdminOtpRequest import AdminOtpRequest
from app.core.configurations import HTTPStatus as status
from app.core.responses import ok_error_response, ok_response

def admin_otp_send_route():
    form = AdminOtpRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        email = data["email"]

        user_id = session.get("user_id")
        if not user_id:
            return ok_error_response("Not authenticated", status.UNAUTHORIZED)

        svc = OtpService()

        if not email:
            try:
                email = svc.get_user_email(str(user_id))
            except Exception:
                email = ""

        if not email:
            return ok_error_response(
                "OTP email not configured. Please set it in Admin Settings."
            )

        msg = svc.send_otp(user_id=str(user_id), email=email)
        return ok_response(msg)
    except Exception as e:
        return ok_error_response(str(e))

def admin_otp_verify_route():
    form = AdminOtpRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        otp = data["otp"]

        user_id = session.get("user_id")
        if not user_id:
            return ok_error_response("Not authenticated", status.UNAUTHORIZED)

        svc = OtpService()
        result = svc.verify_otp(user_id=str(user_id), otp=otp)

        if not result.get("ok"):
            retry_after = result.get("retry_after_seconds")
            attempts_remaining = result.get("attempts_remaining")

            status_code = status.FORBIDDEN
            if result.get("reason") == "cooldown":
                status_code = status.TOO_MANY_REQUESTS

            return ok_error_response(
                result.get("message") or "Invalid/expired OTP.",
                status_code,
                reason=result.get("reason"),
                retry_after_seconds=retry_after,
                attempts_remaining=attempts_remaining,
            )

        session["face_verified"] = True
        return ok_response("OTP verified")
    except Exception as e:
        return ok_error_response(str(e))

def admin_otp_reset_route():
    form = AdminOtpRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:

        session.pop("face_verified", None)
        return ok_response("OTP verification gate cleared")
    except Exception as e:
        return ok_error_response(str(e))

def admin_otp_email_get_route():
    form = AdminOtpRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        user_id = session.get("user_id")
        if not user_id:
            return ok_error_response("Not authenticated", status.UNAUTHORIZED)

        svc = OtpService()
        email = svc.get_user_email(str(user_id))

        retry_after_seconds = svc.get_cooldown_remaining_seconds(str(user_id))

        return ok_response(
            (
                f"Too many invalid attempts. Please wait {retry_after_seconds} seconds and try again."
                if retry_after_seconds and retry_after_seconds > 0
                else ""
            ),
            email=email,
            retry_after_seconds=retry_after_seconds,
        )
    except Exception as e:
        return ok_error_response(str(e))

def admin_otp_email_save_route():
    form = AdminOtpRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        email = data["email"]

        user_id = session.get("user_id")
        if not user_id:
            return ok_error_response("Not authenticated", status.UNAUTHORIZED)

        svc = OtpService()
        svc.update_user_email(str(user_id), email)
        return ok_response("OTP email updated")
    except Exception as e:
        return ok_error_response(str(e))
