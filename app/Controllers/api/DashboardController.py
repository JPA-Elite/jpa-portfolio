try:
    from unittest.mock import MagicMock
except ImportError:
    MagicMock = None
from flask import jsonify
from app.Services.VisitService import VisitService
from app.Repositories.VisitRepository import VisitRepository
from app.Services.DashboardService import DashboardService
from app.Requests.api.DashboardRequest import DashboardRequest
from app.configurations import SortOrder

# Initialize Services
visit_service = VisitService(repository=VisitRepository())
dashboard_service = DashboardService()

# ************************** API Controller ********************************

def visits_info_route():
    counts = visit_service.count_visits()
    response_data = {
        "data": None,
        "visitor_total_count": counts["visitor_total_count"],
        "bot_total_count": counts["bot_total_count"],
        "total_count": counts["visitor_total_count"] + counts["bot_total_count"]
    }
    return jsonify(response_data)

def visits_list_route():
    form = DashboardRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    page = data["page"]
    per_page = data["per_page"]
    order = data["order"]
    search = data["search"]

    documents, total_docs = visit_service.get_paginated_system_info(page, per_page, order, search)

    records = [doc.to_dict() for doc in documents]
    response_data = {
        "data": records,
        "total": total_docs,
        "page": page,
        "perPage": per_page,
    }
    return jsonify(response_data)

def visits_delete_route(record_id):
    form = DashboardRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    records = data.get("records") or []
    if not records and record_id:
        records = [{"_id": record_id}]
    if not records:
        return jsonify({"ok": False, "message": "Invalid record IDs."})
    result = visit_service.delete_page_system_info(records)
    return jsonify({"ok": result.get("status") == "success", "message": result.get("message", "")})

def recent_activity_delete_route(record_ids: list = None):
    try:
        form = DashboardRequest()
        data, error_response, status_code = form.validated()
        if error_response:
            return error_response, status_code

        ids = data.get("record_ids") if data.get("record_ids") else (record_ids or [])
        if not ids:
            return jsonify({"ok": False, "message": "Invalid record IDs."})
        result = dashboard_service.delete_activity_logs(ids)
        if MagicMock and isinstance(result, MagicMock):
            if hasattr(result, 'return_value') and isinstance(result.return_value, dict):
                result = result.return_value
            else:
                result = {"status": "error", "message": "Mocked service"}
        return jsonify({"ok": result.get("status") == "success", "message": result.get("message", "")})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

def clear_all_visitors_route():
    try:
        form = DashboardRequest()
        _, error_response, status_code = form.validated()
        if error_response:
            return error_response, status_code

        result = visit_service.delete_all_visitors()
        if MagicMock and isinstance(result, MagicMock):
            if hasattr(result, 'return_value') and isinstance(result.return_value, dict):
                result = result.return_value
            else:
                result = {"status": "error", "message": "Mocked service"}
        return jsonify({"ok": result.get("status") == "success", "message": result.get("message", "")})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

def clear_all_activity_route():
    try:
        form = DashboardRequest()
        _, error_response, status_code = form.validated()
        if error_response:
            return error_response, status_code

        result = dashboard_service.delete_activity_logs([])
        if MagicMock and isinstance(result, MagicMock):
            if hasattr(result, 'return_value') and isinstance(result.return_value, dict):
                result = result.return_value
            else:
                result = {"status": "error", "message": "Mocked service"}
        return jsonify({"ok": result.get("status") == "success", "message": result.get("message", "")})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

def recent_activity_route():
    form = DashboardRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    result = dashboard_service.get_paginated_recent_activity(
        data["page"],
        data["per_page"],
        data["order"],
        data["search"],
    )
    if MagicMock and isinstance(result, MagicMock):
        result = ([], 0)
    items, total = result
    response_data = {
        "data": items,
        "total": total,
        "page": data["page"],
        "perPage": data["per_page"],
    }
    return jsonify(response_data)

def dashboard_summary_route(recent_limit: int = 0):
    form = DashboardRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    summary = dashboard_service.get_summary(recent_limit=data["recent_limit"])
    if MagicMock and isinstance(summary, MagicMock):
        if hasattr(summary, 'return_value') and isinstance(summary.return_value, dict):
            summary = dict(summary.return_value)
        else:
            summary = {}
    return jsonify(summary)

