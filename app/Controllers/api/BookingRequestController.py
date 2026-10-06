from flask import jsonify
from app.Services.BookingRequestService import BookingRequestService
from app.Repositories.BookingRequestRepository import BookingRequestRepository
from app.Requests.api.BookingRequestRequest import BookingRequestRequest
from app.constants.messages import BOOKING_REQUEST_DELETE_MSG, BOOKING_REQUEST_NOT_FOUND_ERROR

booking_request_service = BookingRequestService(repository=BookingRequestRepository())

def booking_request_list_route():
    form = BookingRequestRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    items, total = booking_request_service.get_paginated_list(
        data["page"], data["per_page"], data["order"], data["search_query"],
    )

    response_data = {
        "booking_requests": [item.to_dict() for item in items],
        "total": total,
        "total_pages": (total + data["per_page"] - 1) // data["per_page"],
        "search": data["search_query"],
    }

    return jsonify(response_data)

def delete_booking_request_route(booking_id):
    form = BookingRequestRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = booking_request_service.delete_booking(booking_id)
    if success:
        return jsonify({"message": BOOKING_REQUEST_DELETE_MSG}), 200
    else:
        return jsonify({"message": BOOKING_REQUEST_NOT_FOUND_ERROR}), 404

def clear_all_booking_requests_route():
    try:
        form = BookingRequestRequest()
        _, error_response, status_code = form.validated()
        if error_response:
            return error_response, status_code

        result = booking_request_service.delete_all_booking_requests()
        return jsonify({"ok": result.get("status") == "success", "message": result.get("message", "")})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})
