from flask import request
from app.Requests.api.BookingRequest import BookingRequest
from app.Services.BookingService import BookingService
from app.Repositories.BookingRequestRepository import BookingRequestRepository
from app.security.ddos_guard import get_request_ip
from app.constants.messages import BOOKING_RATE_LIMIT_ERROR, BOOKING_EMAIL_SENT_MSG, CAPTCHA_VERIFICATION_ERROR
from app.security.hcaptcha import verify_hcaptcha
from app.core.configurations import HTTPStatus as status
from app.core.responses import ok_error_response, ok_response

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
        return ok_error_response(CAPTCHA_VERIFICATION_ERROR)

    try:
        svc = BookingService(repository=BookingRequestRepository())

        allowed, retry_after = svc.check_rate_limit(ip)
        if not allowed:
            minutes = max(1, retry_after // 60)
            return ok_error_response(
                BOOKING_RATE_LIMIT_ERROR.format(retry_after=minutes),
                status.TOO_MANY_REQUESTS,
                retry_after_seconds=retry_after,
            )

        svc.increment_count(ip)
        svc.save_booking(data, ip)
        svc.send_booking_email(data)

        return ok_response(BOOKING_EMAIL_SENT_MSG)
    except Exception as e:
        return ok_error_response(str(e))
