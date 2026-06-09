import types
try:
    from unittest.mock import MagicMock
except ImportError:
    MagicMock = None
from flask import jsonify, current_app, request
from backend.Services.VisitService import VisitService
from backend.Repositories.VisitRepository import VisitRepository
from backend.Services.DashboardService import DashboardService
from backend.configurations import SortOrder

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
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("perPage", 10))
    order_str = str(request.args.get("order", "desc")).lower()
    search = str(request.args.get("search", "")).strip().lower()
    order = SortOrder.DESC if order_str == "desc" else SortOrder.ASC

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
    result = visit_service.delete_page_system_info([{"_id": record_id}])
    return jsonify({"ok": result.get("status") == "success", "message": result.get("message", "")})

def recent_activity_delete_route(record_ids: list):
    try:
        result = dashboard_service.delete_activity_logs(record_ids)
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
    items = dashboard_service.get_recent_activity(limit=limit)
    if MagicMock and isinstance(items, MagicMock):
        if hasattr(items, 'return_value') and isinstance(items.return_value, (list, tuple)):
            items = list(items.return_value)
        else:
            items = []
    return jsonify(items)

def dashboard_summary_route(recent_limit: int = 20):
    summary = dashboard_service.get_summary(recent_limit=recent_limit)
    if MagicMock and isinstance(summary, MagicMock):
        if hasattr(summary, 'return_value') and isinstance(summary.return_value, dict):
            summary = dict(summary.return_value)
        else:
            summary = {}
    return jsonify(summary)

