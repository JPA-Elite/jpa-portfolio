from flask import jsonify, request, session
from app.Repositories.AuthRepository import AuthRepository
from app.Services.OtpService import OtpService
from app.Requests.api.AdminOtpRequest import AdminOtpRequest

def admin_otp_send_route():
    form = AdminOtpRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        email = data["email"]

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        svc = OtpService()

        if not email:
            try:
                user_doc = AuthRepository().find_by_id(str(user_id)) or {}
                email = (user_doc.get("email") or "").strip()
            except Exception:
                email = ""

        if not email:
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "OTP email not configured. Please set it in Admin Settings.",
                    }
                ),
                400,
            )

        msg = svc.send_otp(user_id=str(user_id), email=email)
        return jsonify({"ok": True, "message": msg})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

def admin_otp_verify_route():
    form = AdminOtpRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        otp = data["otp"]

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        svc = OtpService()
        result = svc.verify_otp(user_id=str(user_id), otp=otp)

        if not result.get("ok"):
            retry_after = result.get("retry_after_seconds")
            attempts_remaining = result.get("attempts_remaining")

            status_code = 403
            if result.get("reason") == "cooldown":
                status_code = 429

            return (
                jsonify(
                    {
                        "ok": False,
                        "message": result.get("message") or "Invalid/expired OTP.",
                        "reason": result.get("reason"),
                        "retry_after_seconds": retry_after,
                        "attempts_remaining": attempts_remaining,
                    }
                ),
                status_code,
            )

        session["face_verified"] = True
        return jsonify({"ok": True, "message": "OTP verified"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

def admin_otp_reset_route():
    form = AdminOtpRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:

        session.pop("face_verified", None)
        return jsonify({"ok": True, "message": "OTP verification gate cleared"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

def admin_otp_email_get_route():
    form = AdminOtpRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        user_doc = AuthRepository().find_by_id(str(user_id)) or {}
        email = (user_doc.get("email") or "").strip()

        svc = OtpService()
        retry_after_seconds = svc.get_cooldown_remaining_seconds(str(user_id))

        return jsonify(
            {
                "ok": True,
                "email": email,
                "retry_after_seconds": retry_after_seconds,
                "message": (
                    f"Too many invalid attempts. Please wait {retry_after_seconds} seconds and try again."
                    if retry_after_seconds and retry_after_seconds > 0
                    else ""
                ),
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

def admin_otp_email_save_route():
    form = AdminOtpRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        email = data["email"]

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        AuthRepository().update_user(str(user_id), {"email": email})
        return jsonify({"ok": True, "message": "OTP email updated"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

