import importlib
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import numpy as np
from flask import Flask

from app.Repositories.BaseRepository import BaseRepository


def _fake_get_mongo_client(self, collection_name):
    return object(), {}, MagicMock()


class ApiAdminFaceControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
            cls.module = importlib.import_module(
                "app.Controllers.api.AdminFaceController"
            )

    def setUp(self):
        self.service = MagicMock()
        self.service_patcher = patch.object(self.module, "auth_service", self.service)
        self.service_patcher.start()
        self.addCleanup(self.service_patcher.stop)

        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.app.add_url_rule(
            "/admin/api/face/register",
            endpoint="admin_face_register",
            view_func=self.module.admin_face_register_route,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/admin/api/face/records",
            endpoint="admin_face_records",
            view_func=self.module.admin_face_records_route,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/admin/api/face/verify",
            endpoint="admin_face_verify",
            view_func=self.module.admin_face_verify_route,
            methods=["POST"],
        )
        self.client = self.app.test_client()

    def _login(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "user-1"

    def _face_verified(self):
        with self.client.session_transaction() as session:
            return session.get("face_verified")

    @contextmanager
    def _patched_pipeline(self, distance=10.0, encoded="encoded-face"):
        with patch.object(
            self.module,
            "_decode_b64_image",
            return_value=np.zeros((20, 20, 3), dtype=np.uint8),
        ), patch.object(
            self.module,
            "_detect_and_crop_face",
            return_value=np.zeros((160, 160), dtype=np.uint8),
        ), patch.object(
            self.module,
            "_normalize_face",
            side_effect=lambda image: np.zeros((160, 160), dtype=np.uint8),
        ), patch.object(
            self.module, "_encode_crop_to_b64", return_value=encoded
        ), patch.object(
            self.module,
            "_b64_png_to_gray_160",
            return_value=np.zeros((160, 160), dtype=np.uint8),
        ), patch.object(
            self.module, "_face_l1_distance", return_value=distance
        ):
            yield

    def test_register_requires_image(self):
        self._login()

        response = self.client.post("/admin/api/face/register", json={})

        self.assertEqual(response.status_code, 400)
        self.assertIn("image_b64", response.get_json()["errors"])
        self.service.save_face_reference.assert_not_called()

    def test_register_requires_authenticated_admin(self):
        with self._patched_pipeline():
            response = self.client.post(
                "/admin/api/face/register",
                json={"image_b64_list": ["image-1", "image-2"]},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "Not authenticated"}
        )
        self.service.save_face_reference.assert_not_called()

    def test_register_saves_encoded_reference(self):
        self._login()

        with self._patched_pipeline(encoded="stored-reference"):
            response = self.client.post(
                "/admin/api/face/register",
                json={"image_b64_list": ["image-1", "image-2"]},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"ok": True, "message": "Face reference registered"},
        )
        self.service.save_face_reference.assert_called_once()
        args = self.service.save_face_reference.call_args.args
        self.assertEqual(args[0], "user-1")
        self.assertEqual(args[1], "stored-reference")
        self.assertRegex(args[2], r"^\d{4}-\d{2}-\d{2}T.*Z$")

    def test_register_returns_error_when_image_cannot_be_processed(self):
        self._login()

        with patch.object(
            self.module,
            "_decode_b64_image",
            side_effect=ValueError("Could not decode image"),
        ):
            response = self.client.post(
                "/admin/api/face/register",
                json={"image_b64": "not-an-image"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"ok": False, "message": "Could not decode image"},
        )
        self.service.save_face_reference.assert_not_called()

    def test_records_requires_authenticated_admin(self):
        response = self.client.get("/admin/api/face/records")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "Not authenticated"}
        )
        self.service.get_face_records.assert_not_called()

    def test_records_returns_empty_rows_without_history(self):
        self._login()
        self.service.get_face_records.return_value = {}

        response = self.client.get("/admin/api/face/records")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True, "rows": []})
        self.service.get_face_records.assert_called_once_with("user-1")

    def test_records_returns_registration_and_verification_rows(self):
        self._login()
        self.service.get_face_records.return_value = {
            "face_last_registered_at": "2026-10-20T10:00:00Z",
            "face_last_verified_at": "2026-10-21T11:30:00Z",
            "face_last_verify_distance": 18.5,
        }

        response = self.client.get("/admin/api/face/records")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "ok": True,
                "rows": [
                    {
                        "status": "Registered",
                        "distance": None,
                        "timestamp": "2026-10-20T10:00:00Z",
                    },
                    {
                        "status": "Verified",
                        "distance": 18.5,
                        "timestamp": "2026-10-21T11:30:00Z",
                    },
                ],
            },
        )

    def test_records_returns_error_when_service_raises(self):
        self._login()
        self.service.get_face_records.side_effect = RuntimeError("lookup failed")

        response = self.client.get("/admin/api/face/records")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "lookup failed"}
        )

    def test_verify_requires_image(self):
        self._login()

        response = self.client.post("/admin/api/face/verify", json={})

        self.assertEqual(response.status_code, 400)
        self.service.get_face_records.assert_not_called()

    def test_verify_requires_authenticated_admin(self):
        with self._patched_pipeline():
            response = self.client.post(
                "/admin/api/face/verify", json={"image_b64": "image-1"}
            )

        self.assertEqual(response.status_code, 401)
        self.service.get_face_records.assert_not_called()

    def test_verify_requires_registered_reference(self):
        self._login()
        self.service.get_face_records.return_value = {}

        with self._patched_pipeline():
            response = self.client.post(
                "/admin/api/face/verify", json={"image_b64": "image-1"}
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "ok": False,
                "message": "No registered face found. Please register first.",
            },
        )
        self.service.mark_face_verified.assert_not_called()

    def test_verify_success_marks_face_and_sets_session(self):
        self._login()
        self.service.get_face_records.return_value = {
            "face_reference_crop_b64": "stored-reference"
        }

        with self._patched_pipeline(distance=12.25):
            response = self.client.post(
                "/admin/api/face/verify", json={"image_b64": "image-1"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"ok": True, "message": "Face verified", "distance": 12.25},
        )
        self.assertTrue(self._face_verified())
        self.service.mark_face_verified.assert_called_once()
        args = self.service.mark_face_verified.call_args.args
        self.assertEqual(args[0], "user-1")
        self.assertRegex(args[1], r"^\d{4}-\d{2}-\d{2}T.*Z$")
        self.assertEqual(args[2], 12.25)

    def test_verify_mismatch_returns_forbidden(self):
        self._login()
        self.service.get_face_records.return_value = {
            "face_reference_crop_b64": "stored-reference"
        }

        with self._patched_pipeline(distance=22.01):
            response = self.client.post(
                "/admin/api/face/verify", json={"image_b64": "image-1"}
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.get_json(),
            {
                "ok": False,
                "message": "Face does not match. Please try again.",
                "distance": 22.01,
            },
        )
        self.service.mark_face_verified.assert_not_called()
        self.assertIsNone(self._face_verified())

    def test_verify_returns_error_for_processing_failure(self):
        self._login()

        with patch.object(
            self.module,
            "_decode_b64_image",
            side_effect=ValueError("Could not decode image"),
        ):
            response = self.client.post(
                "/admin/api/face/verify", json={"image_b64": "broken"}
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"ok": False, "message": "Could not decode image"},
        )

    def test_face_distance_is_mean_absolute_pixel_difference(self):
        first = np.zeros((160, 160), dtype=np.uint8)
        second = np.ones((160, 160), dtype=np.uint8)

        self.assertEqual(self.module._face_l1_distance(first, first), 0.0)
        self.assertEqual(self.module._face_l1_distance(first, second), 1.0)


if __name__ == "__main__":
    unittest.main()
