import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.Services.BookingService import BookingService


class BookingServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.cache = MagicMock()
        self.cache_patcher = patch("app.Services.BookingService.cache", self.cache)
        self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)
        self.service = BookingService(repository=self.repo)

    def _booking_data(self, **overrides):
        data = {
            "name": "Joshua",
            "email": "joshua@example.com",
            "preferred_date": "2026-11-02",
            "preferred_time": "13:05",
            "message": "Project discussion",
            "service": "Consultation",
        }
        data.update(overrides)
        return data

    def _configure_smtp(self):
        self.service.smtp_host = "smtp.example.com"
        self.service.smtp_port = 587
        self.service.smtp_username = "admin@example.com"
        self.service.smtp_password = "secret"
        self.service.smtp_from = "admin@example.com"
        self.service.smtp_from_name = "JPA Portfolio"
        self.service.smtp_use_tls = True
        self.service.smtp_use_ssl = False

    def test_constructor_reads_environment_configuration(self):
        env = {
            "SMTP_HOST": "smtp.test",
            "SMTP_PORT": "2525",
            "SMTP_USERNAME": "user",
            "SMTP_PASSWORD": "pass",
            "SMTP_FROM": "from@test",
            "SMTP_FROM_NAME": "Portfolio",
            "SMTP_USE_TLS": "false",
            "SMTP_USE_SSL": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            service = BookingService(repository=self.repo)

        self.assertEqual(service.smtp_host, "smtp.test")
        self.assertEqual(service.smtp_port, 2525)
        self.assertEqual(service.smtp_username, "user")
        self.assertEqual(service.smtp_password, "pass")
        self.assertEqual(service.smtp_from, "from@test")
        self.assertEqual(service.smtp_from_name, "Portfolio")
        self.assertFalse(service.smtp_use_tls)
        self.assertTrue(service.smtp_use_ssl)

    def test_check_rate_limit_allows_requests_below_limit(self):
        self.cache.get.return_value = 9

        allowed, retry_after = self.service.check_rate_limit("203.0.113.5")

        self.assertTrue(allowed)
        self.assertEqual(retry_after, 0)

    def test_check_rate_limit_blocks_requests_at_limit(self):
        self.cache.get.return_value = 10

        with patch("app.Services.BookingService.time.time", return_value=1000):
            allowed, retry_after = self.service.check_rate_limit("203.0.113.5")

        self.assertFalse(allowed)
        self.assertEqual(retry_after, 2600)

    def test_check_rate_limit_uses_remaining_window_time(self):
        self.cache.get.return_value = 15

        with patch("app.Services.BookingService.time.time", return_value=3599):
            allowed, retry_after = self.service.check_rate_limit("203.0.113.5")

        self.assertFalse(allowed)
        self.assertEqual(retry_after, 1)

    def test_increment_count_starts_at_one(self):
        self.cache.get.return_value = None

        count = self.service.increment_count("203.0.113.5")

        self.assertEqual(count, 1)
        key, value = self.cache.set.call_args.args
        self.assertTrue(key.startswith("booking_rate:"))
        self.assertEqual(value, 1)
        self.assertEqual(self.cache.set.call_args.kwargs["timeout"], 3660)

    def test_increment_count_increments_existing_value(self):
        self.cache.get.return_value = 4

        count = self.service.increment_count("203.0.113.5")

        self.assertEqual(count, 5)
        self.assertEqual(self.cache.set.call_args.args[1], 5)

    def test_save_booking_builds_booking_document(self):
        self.service.save_booking(self._booking_data(), "203.0.113.5")

        doc = self.repo.insert_booking.call_args.args[0]
        self.assertEqual(doc["name"], "Joshua")
        self.assertEqual(doc["email"], "joshua@example.com")
        self.assertEqual(doc["preferred_date"], "2026-11-02")
        self.assertEqual(doc["preferred_time"], "13:05")
        self.assertEqual(doc["message"], "Project discussion")
        self.assertEqual(doc["service"], "Consultation")
        self.assertEqual(doc["ip_address"], "203.0.113.5")
        self.assertFalse(doc["read"])
        self.assertIsInstance(doc["created_at"], datetime)

    def test_save_booking_supports_missing_optional_service(self):
        data = self._booking_data()
        data.pop("service")

        self.service.save_booking(data, "203.0.113.5")

        doc = self.repo.insert_booking.call_args.args[0]
        self.assertIsNone(doc["service"])

    def test_format_time_ampm_handles_midnight_noon_and_afternoon(self):
        self.assertEqual(self.service._format_time_ampm("00:05"), "12:05 AM")
        self.assertEqual(self.service._format_time_ampm("09:30"), "9:30 AM")
        self.assertEqual(self.service._format_time_ampm("12:30"), "12:30 PM")
        self.assertEqual(self.service._format_time_ampm("13:07"), "1:07 PM")

    def test_format_time_ampm_returns_invalid_value_unchanged(self):
        self.assertEqual(self.service._format_time_ampm("not-a-time"), "not-a-time")
        self.assertEqual(self.service._format_time_ampm(None), None)

    def test_send_booking_email_uses_starttls_and_message_content(self):
        self._configure_smtp()
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp_cls = MagicMock(return_value=smtp)

        with patch("app.Services.BookingService.smtplib.SMTP", smtp_cls), patch(
            "app.Services.BookingService.ssl.create_default_context",
            return_value="ssl-context",
        ):
            self.service.send_booking_email(self._booking_data())

        smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=15)
        smtp.starttls.assert_called_once_with(context="ssl-context")
        smtp.login.assert_called_once_with("admin@example.com", "secret")
        smtp.send_message.assert_called_once()
        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["To"], "admin@example.com")
        self.assertEqual(message["From"], "JPA Portfolio <admin@example.com>")
        body = message.get_content()
        self.assertIn("Name: Joshua", body)
        self.assertIn("Time: 1:05 PM", body)
        self.assertIn("Service: Consultation", body)

    def test_send_booking_email_uses_ssl_connection_when_enabled(self):
        self._configure_smtp()
        self.service.smtp_use_tls = False
        self.service.smtp_use_ssl = True
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp_cls = MagicMock(return_value=smtp)

        with patch("app.Services.BookingService.smtplib.SMTP_SSL", smtp_cls), patch(
            "app.Services.BookingService.ssl.create_default_context",
            return_value="ssl-context",
        ):
            self.service.send_booking_email(self._booking_data())

        smtp_cls.assert_called_once_with("smtp.example.com", 587, context="ssl-context")
        smtp.starttls.assert_not_called()
        smtp.login.assert_called_once_with("admin@example.com", "secret")
        smtp.send_message.assert_called_once()

    def test_send_booking_email_falls_back_to_smtp_from_recipient(self):
        self._configure_smtp()
        self.service.smtp_username = ""
        self.service.smtp_from = "noreply@example.com"
        self.service.smtp_from_name = ""
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp_cls = MagicMock(return_value=smtp)

        with patch("app.Services.BookingService.smtplib.SMTP", smtp_cls), patch(
            "app.Services.BookingService.ssl.create_default_context",
            return_value="ssl-context",
        ):
            self.service.send_booking_email(self._booking_data(service=None))

        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["To"], "noreply@example.com")
        self.assertEqual(message["From"], "noreply@example.com")
        self.assertNotIn("Service:", message.get_content())


if __name__ == "__main__":
    unittest.main()
