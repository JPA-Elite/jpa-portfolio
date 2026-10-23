import importlib
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from app.Repositories.BaseRepository import BaseRepository


def _fake_get_mongo_client(self, collection_name):
    return object(), {}, MagicMock()


class ApiBookingControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
            cls.module = importlib.import_module("app.Controllers.api.BookingController")

    def setUp(self):
        self.repository = MagicMock()
        self.repository_cls = MagicMock(return_value=self.repository)
        self.service = MagicMock()
        self.service_cls = MagicMock(return_value=self.service)
        self.verify_hcaptcha = MagicMock(return_value=(True, {}))
        self.get_request_ip = MagicMock(return_value="203.0.113.5")

        self.patchers = [
            patch.object(self.module, "BookingRequestRepository", self.repository_cls),
            patch.object(self.module, "BookingService", self.service_cls),
            patch.object(self.module, "verify_hcaptcha", self.verify_hcaptcha),
            patch.object(self.module, "get_request_ip", self.get_request_ip),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.service.check_rate_limit.return_value = (True, 0)

        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.app.add_url_rule(
            "/api/booking/send",
            endpoint="booking_send",
            view_func=self.module.booking_send_route,
            methods=["POST"],
        )
        self.client = self.app.test_client()

    def _payload(self, **overrides):
        payload = {
            "name": "Joshua Algadipe",
            "email": "joshua@example.com",
            "preferred_date": "2026-11-02",
            "preferred_time": "13:05",
            "message": "I would like to discuss a project.",
            "service": "Consultation",
            "hcaptcha_token": "captcha-token",
        }
        payload.update(overrides)
        return payload

    def test_booking_success_saves_and_sends_email(self):
        response = self.client.post("/api/booking/send", json=self._payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "ok": True,
                "message": "Your booking request has been sent successfully! We will contact you shortly.",
            },
        )
        self.repository_cls.assert_called_once_with()
        self.service_cls.assert_called_once_with(repository=self.repository)
        self.verify_hcaptcha.assert_called_once_with(
            "captcha-token", remote_ip="203.0.113.5"
        )
        self.get_request_ip.assert_called_once_with()
        self.service.check_rate_limit.assert_called_once_with("203.0.113.5")
        self.service.increment_count.assert_called_once_with("203.0.113.5")
        expected_data = {
            "name": "Joshua Algadipe",
            "email": "joshua@example.com",
            "preferred_date": "2026-11-02",
            "preferred_time": "13:05",
            "message": "I would like to discuss a project.",
            "service": "Consultation",
        }
        self.service.save_booking.assert_called_once_with(
            expected_data, "203.0.113.5"
        )
        self.service.send_booking_email.assert_called_once_with(expected_data)

    def test_booking_trims_captcha_token(self):
        response = self.client.post(
            "/api/booking/send",
            json=self._payload(hcaptcha_token="  token-with-spaces  "),
        )

        self.assertEqual(response.status_code, 200)
        self.verify_hcaptcha.assert_called_once_with(
            "token-with-spaces", remote_ip="203.0.113.5"
        )

    def test_booking_rejects_invalid_fields_before_side_effects(self):
        cases = [
            ({"name": ""}, "name"),
            ({"name": "x" * 51}, "name"),
            ({"email": ""}, "email"),
            ({"email": "not-an-email"}, "email"),
            ({"preferred_date": ""}, "preferred_date"),
            ({"preferred_time": ""}, "preferred_time"),
            ({"message": ""}, "message"),
            ({"message": "x" * 501}, "message"),
        ]

        for overrides, field in cases:
            with self.subTest(field=field, overrides=overrides):
                self.service_cls.reset_mock()
                self.verify_hcaptcha.reset_mock()

                response = self.client.post(
                    "/api/booking/send", json=self._payload(**overrides)
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.get_json()["errors"])
                self.verify_hcaptcha.assert_not_called()
                self.service_cls.assert_not_called()

    def test_booking_rejects_failed_captcha(self):
        self.verify_hcaptcha.return_value = (False, {"error": "invalid"})

        response = self.client.post("/api/booking/send", json=self._payload())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "ok": False,
                "message": "Captcha verification failed. Please try again.",
            },
        )
        self.service_cls.assert_not_called()

    def test_booking_returns_rate_limit_response(self):
        self.service.check_rate_limit.return_value = (False, 125)

        response = self.client.post("/api/booking/send", json=self._payload())

        self.assertEqual(response.status_code, 429)
        payload = response.get_json()
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["retry_after_seconds"], 125)
        self.assertIn("2 minute(s)", payload["message"])
        self.service.increment_count.assert_not_called()
        self.service.save_booking.assert_not_called()
        self.service.send_booking_email.assert_not_called()

    def test_booking_rate_limit_uses_minimum_one_minute(self):
        self.service.check_rate_limit.return_value = (False, 20)

        response = self.client.post("/api/booking/send", json=self._payload())

        self.assertEqual(response.status_code, 429)
        self.assertIn("1 minute(s)", response.get_json()["message"])

    def test_booking_returns_json_error_when_service_raises(self):
        self.service.check_rate_limit.side_effect = RuntimeError("rate service down")

        response = self.client.post("/api/booking/send", json=self._payload())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "rate service down"}
        )
        self.service.increment_count.assert_not_called()


if __name__ == "__main__":
    unittest.main()
