from flask import jsonify
from Services.VisitService import VisitService
from Services.VisitService import VisitService
from Repositories.VisitRepository import VisitRepository

# Initialize Services
visit_service = VisitService(repository=VisitRepository())

# ************************** API Controller ********************************

def visits_info_route():
    count = visit_service.count_visits()
    return jsonify({
        "data": None,
        "count": count
    })
