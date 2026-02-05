from flask import Flask

from backend.Controllers.api import DashboardController as controller


class _FakeVisitService:
    def count_visits(self):
        return {"visitor_total_count": 7, "bot_total_count": 3}


def test_visits_info_route_returns_expected_payload(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(controller, "visit_service", _FakeVisitService())

    with app.app_context():
        response = controller.visits_info_route()

    data = response.get_json()

    assert response.status_code == 200
    assert data == {
        "data": None,
        "visitor_total_count": 7,
        "bot_total_count": 3,
        "total_count": 10,
    }
