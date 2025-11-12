from flask import jsonify
from Services.VisitService import VisitService
from Services.VisitService import VisitService
from Repositories.VisitRepository import VisitRepository

# Initialize Services
visit_service = VisitService(repository=VisitRepository())

# ************************** API Controller ********************************

def visits_info_route():
    counts = visit_service.count_visits()
    return jsonify({
        "data": None,
        "visitor_total_count": counts["visitor_total_count"],
        "bot_total_count": counts["bot_total_count"],
        "total_count": counts["visitor_total_count"] + counts["bot_total_count"]
    })
