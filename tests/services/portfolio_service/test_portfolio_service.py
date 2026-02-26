import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.Services.PortfolioService import PortfolioService
from backend.constants.messages import SYSTEM_INFO_ADD_MSG

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

    @patch("backend.Services.PortfolioService.requests.get")
    def test_get_ip_location_returns_api_data(self, mock_get):
        mock_get.return_value = SimpleNamespace(
            json=lambda: {"city": "Cebu", "region": "Central Visayas", "country": "PH", "loc": "10,20"}
        )

        result = self.service.get_ip_location("1.2.3.4")

        self.assertEqual(result["ip"], "1.2.3.4")
        self.assertEqual(result["city"], "Cebu")
        self.assertEqual(result["location"], "10,20")

    @patch("backend.Services.PortfolioService.requests.get", side_effect=Exception("network"))
    def test_get_ip_location_returns_unknown_when_request_fails(self, _mock_get):
        result = self.service.get_ip_location("1.2.3.4")

        self.assertEqual(result["ip"], "1.2.3.4")
        self.assertEqual(result["city"], "Unknown")
        self.assertEqual(result["country"], "Unknown")

    @patch("backend.Services.PortfolioService.url_for", return_value="/profile")
    @patch("backend.Services.PortfolioService.platform.architecture", return_value=("64bit", ""))
    @patch("backend.Services.PortfolioService.platform.platform", return_value="Windows-11")
    @patch("backend.Services.PortfolioService.platform.version", return_value="Version")
    @patch("backend.Services.PortfolioService.platform.release", return_value="11")
    @patch("backend.Services.PortfolioService.platform.node", return_value="PC")
    @patch("backend.Services.PortfolioService.platform.system", return_value="Windows")
    @patch("backend.Services.PortfolioService.parse")
    @patch.object(PortfolioService, "get_ip_location")
    @patch.object(PortfolioService, "get_client_ip")
    def test_add_system_info_returns_success_payload_and_saves_record(
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
        _mock_url_for,
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
        self.repo.insert_system_info.return_value = SimpleNamespace(inserted_id=VALID_OBJECT_ID)

        with self.app.test_request_context("/profile", headers={"User-Agent": "UA"}):
            result = self.service.add_system_info(cloudinary_url="/capture.png")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], SYSTEM_INFO_ADD_MSG)
        self.assertEqual(result["id"], VALID_OBJECT_ID)
        saved_doc = self.repo.insert_system_info.call_args[0][0]
        self.assertEqual(saved_doc["user_agent"], "UA")
        self.assertEqual(saved_doc["page"], "/profile")
        self.assertEqual(saved_doc["image_capture"], "/capture.png")
        self.assertEqual(saved_doc["city"], "Cebu")


if __name__ == "__main__":
    unittest.main()
