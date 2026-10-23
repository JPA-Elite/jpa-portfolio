import importlib
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from flask import Flask

from app.Models.BookingRequest import BookingRequest
from app.Repositories.BaseRepository import BaseRepository
from app.configurations import SortOrder


def _fake_get_mongo_client(self, collection_name):
    return object(), {}, MagicMock()


def _booking(name="Joshua", email="joshua@example.com"):
    return BookingRequest(
        _id="booking-1",
        name=name,
        email=email,
        preferred_date="2026-11-02",
        preferred_time="13:05",
        message="Project discussion",
        ip_address="203.0.113.5",
        created_at=datetime(2026, 10, 23, 4, 30),
        service="Consultation",
    )


class ApiBookingRequestControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
            cls.module = importlib.import_module(
                "app.Controllers.api.BookingRequestController"
            )

    def setUp(self):
        self.service = MagicMock()
        self.service_patcher = patch.object(
            self.module, "booking_request_service", self.service
        )
        self.service_patcher.start()
        self.addCleanup(self.service_patcher.stop)

        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.app.add_url_rule(
            "/admin/api/booking-requests",
            endpoint="booking_requests",
            view_func=self.module.booking_request_list_route,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/admin/api/delete-booking-request/<booking_id>",
            endpoint="delete_booking_request",
            view_func=self.module.delete_booking_request_route,
            methods=["DELETE"],
        )
        self.app.add_url_rule(
            "/admin/api/clear-all-booking-requests",
            endpoint="clear_all_booking_requests",
            view_func=self.module.clear_all_booking_requests_route,
            methods=["DELETE"],
        )
        self.client = self.app.test_client()

    def test_list_returns_paginated_booking_requests(self):
        self.service.get_paginated_list.return_value = ([_booking()], 3)

        response = self.client.get(
            "/admin/api/booking-requests?page=2&per_page=2&search=%20joshua%20&order=desc"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["total"], 3)
        self.assertEqual(payload["total_pages"], 2)
        self.assertEqual(payload["search"], "joshua")
        self.assertEqual(len(payload["booking_requests"]), 1)
        self.assertEqual(payload["booking_requests"][0]["name"], "Joshua")
        self.assertEqual(
            payload["booking_requests"][0]["service"], "Consultation"
        )
        self.service.get_paginated_list.assert_called_once_with(
            2, 2, SortOrder.DESC, "joshua"
        )

    def test_list_uses_default_pagination_values(self):
        self.service.get_paginated_list.return_value = ([], 0)

        response = self.client.get("/admin/api/booking-requests")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "booking_requests": [],
                "total": 0,
                "total_pages": 0,
                "search": "",
            },
        )
        self.service.get_paginated_list.assert_called_once_with(
            1, 10, SortOrder.DESC, ""
        )

    def test_list_normalizes_invalid_numbers_and_ascending_order(self):
        self.service.get_paginated_list.return_value = ([], 0)

        response = self.client.get(
            "/admin/api/booking-requests?page=bad&per_page=bad&order=asc"
        )

        self.assertEqual(response.status_code, 200)
        self.service.get_paginated_list.assert_called_once_with(
            1, 10, SortOrder.ASC, ""
        )

    def test_list_calculates_zero_total_pages_for_empty_result(self):
        self.service.get_paginated_list.return_value = ([], 0)

        response = self.client.get("/admin/api/booking-requests?page=4&per_page=5")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_pages"], 0)

    def test_delete_returns_success_when_deleted(self):
        self.service.delete_booking.return_value = True

        response = self.client.delete(
            "/admin/api/delete-booking-request/booking-1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), {"message": "Booking request deleted successfully"}
        )
        self.service.delete_booking.assert_called_once_with("booking-1")

    def test_delete_returns_not_found_when_missing(self):
        self.service.delete_booking.return_value = False

        response = self.client.delete(
            "/admin/api/delete-booking-request/missing"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json(), {"message": "Booking request not found"}
        )

    def test_clear_all_returns_success_result(self):
        self.service.delete_all_booking_requests.return_value = {
            "status": "success",
            "message": "Deleted 2 booking request(s).",
            "deleted_count": 2,
        }

        response = self.client.delete("/admin/api/clear-all-booking-requests")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"ok": True, "message": "Deleted 2 booking request(s)."},
        )

    def test_clear_all_returns_error_result_as_ok_false(self):
        self.service.delete_all_booking_requests.return_value = {
            "status": "error",
            "message": "Delete failed.",
        }

        response = self.client.delete("/admin/api/clear-all-booking-requests")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "Delete failed."}
        )

    def test_clear_all_returns_json_error_when_service_raises(self):
        self.service.delete_all_booking_requests.side_effect = RuntimeError("boom")

        response = self.client.delete("/admin/api/clear-all-booking-requests")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "boom"}
        )


if __name__ == "__main__":
    unittest.main()
