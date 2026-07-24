from flask import jsonify
from app.Requests.api.BookingRequest import BookingRequest
from app.Services.BookingService import BookingService
from app.security.ddos_guard import get_request_ip
from app.constants.messages import BOOKING_RATE_LIMIT_ERROR, BOOKING_EMAIL_SENT_MSG

def booking_send_route():
    form = BookingRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    try:
        ip = get_request_ip()
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
