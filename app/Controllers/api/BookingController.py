from flask import jsonify, request
from app.Requests.api.BookingRequest import BookingRequest
from app.Services.BookingService import BookingService
from app.security.ddos_guard import get_request_ip
from app.constants.messages import BOOKING_RATE_LIMIT_ERROR, BOOKING_EMAIL_SENT_MSG, CAPTCHA_VERIFICATION_ERROR
from app.utils import verify_hcaptcha

def booking_send_route():
    form = BookingRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    payload = request.get_json(silent=True) or {}
    hcaptcha_token = str(payload.get("hcaptcha_token", "")).strip()
    ip = get_request_ip()
    ok, _details = verify_hcaptcha(hcaptcha_token, remote_ip=ip)
    if not ok:
        return jsonify({"ok": False, "message": CAPTCHA_VERIFICATION_ERROR}), 400

    try:
        svc = BookingService()

        allowed, retry_after = svc.check_rate_limit(ip)
        if not allowed:
            minutes = max(1, retry_after // 60)
            return jsonify({
                "ok": False,
                "message": BOOKING_RATE_LIMIT_ERROR.format(retry_after=minutes),
                "retry_after_seconds": retry_after,
            }), 429

        svc.increment_count(ip)
        svc.save_booking(data, ip)
        svc.send_booking_email(data)

        return jsonify({"ok": True, "message": BOOKING_EMAIL_SENT_MSG})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400
