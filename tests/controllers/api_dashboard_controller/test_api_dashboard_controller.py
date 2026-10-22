import importlib
import unittest
from unittest.mock import patch

from flask import Flask

from app.Repositories.BaseRepository import BaseRepository
from tests.controllers.shared._controller_test_helpers import (
    _fake_get_mongo_client,
    run_controller_module_functions_test,
    run_controller_module_smoke_test,
)


class ApiDashboardControllerModuleTests(unittest.TestCase):
    def test_module_import_and_public_functions(self):
        run_controller_module_smoke_test(self, "app.Controllers.api.DashboardController")

    def test_all_public_functions_execute(self):
        run_controller_module_functions_test(self, "app.Controllers.api.DashboardController")


class ApiDashboardControllerClearVisitorsTests(unittest.TestCase):
    def test_clear_all_visitors_route_returns_ok_for_dict_result(self):
        app = Flask(__name__)
        with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
            module = importlib.import_module("app.Controllers.api.DashboardController")

        app.add_url_rule(
            "/admin/api/clear-all-visitors",
            endpoint="clear_all_visitors",
            view_func=module.clear_all_visitors_route,
            methods=["DELETE"],
        )

        with patch.object(
            module.visit_service,
            "delete_all_visitors",
            return_value={"status": "success", "message": "All visitors cleared."},
        ):
            with app.test_request_context("/admin/api/clear-all-visitors", method="DELETE"):
                response = module.clear_all_visitors_route()

        self.assertEqual(response.get_json(), {"ok": True, "message": "All visitors cleared."})


if __name__ == "__main__":
    unittest.main()
