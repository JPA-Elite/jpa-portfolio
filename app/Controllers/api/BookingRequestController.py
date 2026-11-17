from app.Services.BookingRequestService import BookingRequestService
from app.Repositories.BookingRequestRepository import BookingRequestRepository
from app.Requests.api.BookingRequestRequest import BookingRequestRequest
from app.constants.messages import BOOKING_REQUEST_DELETE_MSG, BOOKING_REQUEST_NOT_FOUND_ERROR
from app.core.configurations import HTTPStatus as status
from app.core.responses import json_response, message_response, ok_error_response, result_response

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

    return json_response(response_data)

def delete_booking_request_route(booking_id):
    form = BookingRequestRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = booking_request_service.delete_booking(booking_id)
    if success:
        return message_response(BOOKING_REQUEST_DELETE_MSG)
    else:
        return message_response(BOOKING_REQUEST_NOT_FOUND_ERROR, status.NOT_FOUND)

def clear_all_booking_requests_route():
    try:
        form = BookingRequestRequest()
        _, error_response, status_code = form.validated()
        if error_response:
            return error_response, status_code

        result = booking_request_service.delete_all_booking_requests()
        return result_response(result)
    except Exception as e:
        return ok_error_response(str(e), status.OK)
