import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.Services.PortfolioService import PortfolioService
from app.constants.messages import SYSTEM_INFO_ADD_MSG, VISIT_ALREADY_RECORDED_MSG

from tests.services._service_fixtures import build_test_app
from tests.test_support import VALID_OBJECT_ID


class PortfolioServiceTests(unittest.TestCase):
    def setUp(self):
        self.app = build_test_app()
        self.repo = MagicMock()
        self.service = PortfolioService(repository=self.repo)

    def test_get_client_ip_uses_first_forwarded_ip(self):
        with self.app.test_request_context("/profile", headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}):
            client_ip = self.service.get_client_ip()

        self.assertEqual(client_ip, "1.2.3.4")

    @patch("app.Services.PortfolioService.requests.get")
    def test_get_ip_location_returns_api_data(self, mock_get):
        mock_get.return_value = SimpleNamespace(
            json=lambda: {"city": "Cebu", "region": "Central Visayas", "country": "PH", "loc": "10,20"}
        )

        result = self.service.get_ip_location("1.2.3.4")

        self.assertEqual(result["ip"], "1.2.3.4")
        self.assertEqual(result["city"], "Cebu")
        self.assertEqual(result["location"], "10,20")

    @patch("app.Services.PortfolioService.requests.get", side_effect=Exception("network"))
    def test_get_ip_location_returns_unknown_when_request_fails(self, _mock_get):
        result = self.service.get_ip_location("1.2.3.4")

        self.assertEqual(result["ip"], "1.2.3.4")
        self.assertEqual(result["city"], "Unknown")
        self.assertEqual(result["country"], "Unknown")

    @patch("app.Services.PortfolioService.platform.architecture", return_value=("64bit", ""))
    @patch("app.Services.PortfolioService.platform.platform", return_value="Windows-11")
    @patch("app.Services.PortfolioService.platform.version", return_value="Version")
    @patch("app.Services.PortfolioService.platform.release", return_value="11")
    @patch("app.Services.PortfolioService.platform.node", return_value="PC")
    @patch("app.Services.PortfolioService.platform.system", return_value="Windows")
    @patch("app.Services.PortfolioService.parse")
    @patch.object(PortfolioService, "get_ip_location")
    @patch.object(PortfolioService, "get_client_ip")
    def test_record_visit_saves_record_once(
        self,
        mock_get_client_ip,
        mock_get_ip_location,
        mock_parse,
        _mock_system,
        _mock_node,
        _mock_release,
        _mock_version,
        _mock_platform,
        _mock_architecture,
    ):
        mock_get_client_ip.return_value = "1.2.3.4"
        mock_get_ip_location.return_value = {
            "ip": "1.2.3.4",
            "city": "Cebu",
            "region": "Central Visayas",
            "country": "PH",
            "location": "10,20",
        }
        mock_parse.return_value = SimpleNamespace(
            device=SimpleNamespace(family="Phone", brand="Brand", model="Model"),
            browser=SimpleNamespace(family="Chrome", version_string="1.0"),
            os=SimpleNamespace(family="Android", version_string="14"),
        )
        self.repo.find_visit_for_day.return_value = None
        self.repo.insert_system_info.return_value = SimpleNamespace(inserted_id=VALID_OBJECT_ID)

        with self.app.test_request_context("/gallery", headers={"User-Agent": "UA"}):
            result = self.service.record_visit(page="/gallery")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], SYSTEM_INFO_ADD_MSG)
        self.assertEqual(result["id"], VALID_OBJECT_ID)
        saved_doc = self.repo.insert_system_info.call_args[0][0]
        self.assertEqual(saved_doc["user_agent"], "UA")
        self.assertEqual(saved_doc["page"], "/gallery")
        self.assertEqual(saved_doc["city"], "Cebu")
        self.assertIsNotNone(saved_doc["visit_date"])
        self.assertTrue(str(saved_doc["occurred_at"]).endswith("+08:00"))
        self.assertRegex(saved_doc["timestamp"], r"^\d{2}/\d{2}/\d{4} - \d{2}:\d{2} [AP]M$")
        self.assertIsNone(saved_doc["image_capture"])

    @patch("app.Services.PortfolioService.parse")
    @patch.object(PortfolioService, "get_client_ip")
    def test_record_visit_skips_when_already_recorded_today(self, mock_get_client_ip, _mock_parse):
        mock_get_client_ip.return_value = "1.2.3.4"
        self.repo.find_visit_for_day.return_value = {"_id": VALID_OBJECT_ID}

        with self.app.test_request_context("/gallery", headers={"User-Agent": "UA"}):
            result = self.service.record_visit(page="/gallery")

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["message"], VISIT_ALREADY_RECORDED_MSG)
        self.repo.insert_system_info.assert_not_called()
        self.repo.find_visit_for_day.assert_called_once()
        passed_ip, passed_page, passed_date = self.repo.find_visit_for_day.call_args[0]
        self.assertEqual(passed_ip, "1.2.3.4")
        self.assertEqual(passed_page, "/gallery")
        self.assertRegex(passed_date, r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
