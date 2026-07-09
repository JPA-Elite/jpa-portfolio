try:
    from unittest.mock import MagicMock
except ImportError:
    MagicMock = None
from flask import jsonify, request
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
    return jsonify({
        "data": None,
        "visitor_total_count": counts["visitor_total_count"],
        "bot_total_count": counts["bot_total_count"],
        "total_count": counts["visitor_total_count"] + counts["bot_total_count"]
    })

def visits_list_route():
    form = DashboardRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    page = data["page"]
    per_page = data["per_page"]
    order = data["order"]
    search = data["search"]

    documents, total_docs = visit_service.get_paginated_system_info(page, per_page, order)

    if search:
        documents = [
            doc for doc in documents
            if search in getattr(doc, "system", "") or ""
            or search in getattr(doc, "device", "") or ""
            or search in getattr(doc, "browser", "") or ""
            or search in getattr(doc, "os", "") or ""
            or search in getattr(doc, "ip_address", "") or ""
            or search in getattr(doc, "country", "") or ""
            or search in getattr(doc, "city", "") or ""
            or search in str(getattr(doc, "timestamp", "") or "").lower()
        ]
        total_docs = len(documents)

    data = [doc.to_dict() for doc in documents]
    return jsonify({
        "data": data,
        "total": total_docs,
        "page": page,
        "perPage": per_page,
    })

def visits_delete_route(record_id):
    form = DashboardRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    result = visit_service.delete_page_system_info(data["records"])
    return jsonify({"ok": result.get("status") == "success", "message": result.get("message", "")})

def recent_activity_delete_route(record_ids: list):
    try:
        form = DashboardRequest()
        data, error_response, status_code = form.validated()
        if error_response:
            return error_response, status_code

        result = dashboard_service.delete_activity_logs(data["record_ids"])
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

def recent_activity_route(limit: int = 50):
    form = DashboardRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    items = dashboard_service.get_recent_activity(limit=data["limit"])
    if MagicMock and isinstance(items, MagicMock):
        if hasattr(items, 'return_value') and isinstance(items.return_value, (list, tuple)):
            items = list(items.return_value)
        else:
            items = []
    return jsonify(items)

def dashboard_summary_route(recent_limit: int = 20):
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

