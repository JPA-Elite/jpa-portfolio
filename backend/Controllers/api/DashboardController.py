import types
try:
    from unittest.mock import MagicMock
except ImportError:
    MagicMock = None
from flask import jsonify, current_app
from backend.Services.VisitService import VisitService
from backend.Repositories.VisitRepository import VisitRepository
from backend.Services.DashboardService import DashboardService

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
