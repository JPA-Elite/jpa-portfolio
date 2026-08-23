import unittest
import io
from unittest.mock import MagicMock, patch

from PIL import Image
from werkzeug.datastructures import FileStorage, MultiDict

from app.Services.BuiltAppService import BuiltAppService
from app.configurations import SortOrder

from tests.services._service_fixtures import built_app_doc


def _png_file_storage():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 6), "blue").save(buffer, "PNG")
    buffer.seek(0)
    return FileStorage(stream=buffer, filename="snap.png", content_type="image/png")


class BuiltAppServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.repo.find.return_value = []
        self.service = BuiltAppService(repository=self.repo)

    def test_get_built_app_by_id_returns_repository_value(self):
        self.repo.get_built_app_by_id.return_value = built_app_doc()

        result = self.service.get_built_app_by_id("app1")

        self.assertEqual(result["slug"], "taskflow")
        self.repo.get_built_app_by_id.assert_called_once_with("app1")

    def test_get_paginated_built_apps_maps_models(self):
        self.repo.get_paginated_built_apps.return_value = ([built_app_doc()], 1)

        items, total = self.service.get_paginated_built_apps(1, 10, SortOrder.DESC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].slug, "taskflow")
        self.assertEqual(items[0].name["en"], "TaskFlow")
        self.repo.get_paginated_built_apps.assert_called_once_with(
            1,
            10,
            SortOrder.DESC,
            "",
            platform_filter="",
            is_active_filter=None,
        )

    def test_get_paginated_built_apps_forwards_filters(self):
        self.repo.get_paginated_built_apps.return_value = ([built_app_doc()], 1)

        self.service.get_paginated_built_apps(
            2,
            5,
            SortOrder.ASC,
            "task",
            platform_filter="mobile",
            is_active_filter=False,
        )

        self.repo.get_paginated_built_apps.assert_called_once_with(
            2,
            5,
            SortOrder.ASC,
            "task",
            platform_filter="mobile",
            is_active_filter=False,
        )

    def test_get_active_built_apps_maps_models(self):
        self.repo.get_active_built_apps.return_value = [built_app_doc()]

        items = self.service.get_active_built_apps()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].platform, "Mobile")
        self.assertEqual(items[0].version, "v1.2.0")

    def test_get_active_built_app_by_slug_returns_none_when_missing(self):
        self.repo.find_active_built_app_by_slug.return_value = None

        result = self.service.get_active_built_app_by_slug("missing")

        self.assertIsNone(result)
        self.repo.find_active_built_app_by_slug.assert_called_once_with("missing")

    def test_add_built_app_without_files_saves_model_with_slug_and_snapshots(self):
        self.repo.add_built_app.return_value = "app-new"

        result = self.service.add_built_app(
            {
                "name": {"en": "TaskFlow"},
                "short_description": {"en": "Task manager."},
                "full_description": {"en": ["Paragraph."]},
                "platform": "Mobile",
                "version": "v1.0.0",
                "snapshot_files": None,
                "snapshots_meta": None,
            }
        )

        self.assertEqual(result, "app-new")
        saved = self.repo.add_built_app.call_args[0][0].to_dict()
        self.assertTrue(saved["id"])
        self.assertEqual(saved["slug"], "taskflow")
        self.assertEqual(saved["snapshots"], [])
        self.assertTrue(saved["is_active"])

    def test_add_built_app_generates_unique_slug_suffix(self):
        self.repo.find.return_value = [{"_id": "x", "slug": "taskflow"}]
        self.repo.add_built_app.return_value = "app-new"

        self.service.add_built_app(
            {
                "name": {"en": "TaskFlow"},
                "snapshot_files": None,
                "snapshots_meta": None,
            }
        )

        saved = self.repo.add_built_app.call_args[0][0].to_dict()
        self.assertEqual(saved["slug"], "taskflow-2")

    def test_add_built_app_persists_snapshots_from_files_mapping(self):
        self.repo.add_built_app.return_value = "app-new"

        files = MultiDict([("snapshot_files", _png_file_storage())])
        with patch.object(
            self.service, "_upload_snapshot_file", return_value="/uploaded.webp"
        ) as mock_upload:
            result = self.service.add_built_app(
                {
                    "name": {"en": "TaskFlow"},
                    "snapshot_files": files,
                    "snapshots_meta": None,
                }
            )

            self.assertEqual(result, "app-new")
            mock_upload.assert_called_once()
        saved = self.repo.add_built_app.call_args[0][0].to_dict()
        self.assertEqual(len(saved["snapshots"]), 1)
        self.assertEqual(saved["snapshots"][0]["image_url"], "/uploaded.webp")
        self.assertEqual(saved["snapshots"][0]["sort_order"], 0)

    def test_update_built_app_replaces_snapshot_via_files_mapping(self):
        existing = built_app_doc()
        existing["snapshots"] = [
            {
                "id": "s1",
                "image_url": "https://res.cloudinary.com/demo/image/upload/old.webp",
                "sort_order": 0,
            }
        ]
        self.repo.get_built_app_by_id.return_value = existing
        self.repo.update_built_app.return_value = True

        with patch.object(
            self.service, "_upload_snapshot_file", return_value="/uploaded.webp"
        ) as mock_upload:
            files = MultiDict([("new_0", _png_file_storage())])
            result = self.service.update_built_app(
                "app1",
                {
                    "snapshots_meta": [{"id": "s1", "image_field": "new_0"}],
                    "snapshot_files": files,
                },
            )

            self.assertTrue(result)
            mock_upload.assert_called_once()

        updated = self.repo.update_built_app.call_args[0][1].to_dict()
        self.assertEqual(len(updated["snapshots"]), 1)
        self.assertEqual(updated["snapshots"][0]["image_url"], "/uploaded.webp")
        self.assertEqual(updated["snapshots"][0]["id"], "s1")

    def test_update_built_app_appends_new_snapshot_row_without_id(self):
        existing = built_app_doc()
        self.repo.get_built_app_by_id.return_value = existing
        self.repo.update_built_app.return_value = True

        with patch.object(
            self.service, "_upload_snapshot_file", return_value="/uploaded.webp"
        ):
            files = MultiDict([("new_0", _png_file_storage())])
            result = self.service.update_built_app(
                "app1",
                {
                    "snapshots_meta": [{"id": None, "image_field": "new_0"}],
                    "snapshot_files": files,
                },
            )

        self.assertTrue(result)
        updated = self.repo.update_built_app.call_args[0][1].to_dict()
        self.assertEqual(len(updated["snapshots"]), 1)
        self.assertTrue(updated["snapshots"][0]["id"])

    def test_update_built_app_returns_false_when_missing(self):
        self.repo.get_built_app_by_id.return_value = None

        result = self.service.update_built_app("app1", {"name": {"en": "New"}})

        self.assertFalse(result)
        self.repo.update_built_app.assert_not_called()

    def test_update_built_app_keeps_existing_snapshots_without_meta(self):
        existing = built_app_doc()
        existing["snapshots"] = [{"id": "s1", "image_url": "/snap.webp", "sort_order": 0}]
        self.repo.get_built_app_by_id.return_value = existing
        self.repo.update_built_app.return_value = True

        result = self.service.update_built_app("app1", {"name": {"en": "Updated"}})

        self.assertTrue(result)
        updated = self.repo.update_built_app.call_args[0][1].to_dict()
        self.assertEqual(updated["name"]["en"], "Updated")
        self.assertEqual(updated["snapshots"], existing["snapshots"])

    def test_delete_built_app_returns_false_when_missing(self):
        self.repo.get_built_app_by_id.return_value = None

        result = self.service.delete_built_app("app1")

        self.assertFalse(result)
        self.repo.delete_built_app.assert_not_called()

    def test_delete_built_app_cleans_snapshot_images(self):
        existing = built_app_doc()
        existing["snapshots"] = [
            {"id": "s1", "image_url": "https://res.cloudinary.com/demo/image/upload/s1.webp", "sort_order": 0},
            {"id": "s2", "image_url": None, "sort_order": 1},
        ]
        self.repo.get_built_app_by_id.return_value = existing
        self.repo.delete_built_app.return_value = True

        with patch.object(self.service, "_cleanup_image_url") as mock_cleanup:
            result = self.service.delete_built_app("app1")

        self.assertTrue(result)
        mock_cleanup.assert_called_once_with("https://res.cloudinary.com/demo/image/upload/s1.webp")
        self.repo.delete_built_app.assert_called_once_with("app1")

    def test_seed_returns_zero_when_collection_not_empty(self):
        self.repo.count_built_apps.return_value = 3

        result = self.service.seed_default_built_apps_if_empty()

        self.assertEqual(result, 0)
        self.repo.add_many_built_apps.assert_not_called()

    def test_seed_inserts_all_default_apps_when_empty(self):
        from app.constants.built_apps import BUILT_APPS

        self.repo.count_built_apps.return_value = 0
        self.repo.add_many_built_apps.return_value = ["id"] * len(BUILT_APPS)

        result = self.service.seed_default_built_apps_if_empty()

        self.assertEqual(result, len(BUILT_APPS))
        seeded = self.repo.add_many_built_apps.call_args[0][0]
        self.assertEqual(len(seeded), len(BUILT_APPS))
        first = seeded[0].to_dict()
        self.assertEqual(first["slug"], BUILT_APPS[0]["slug"])
        self.assertEqual(first["name"]["en"], BUILT_APPS[0]["name"])
        self.assertEqual(first["name"]["ceb"], BUILT_APPS[0]["name"])
        self.assertEqual(first["full_description"]["en"], BUILT_APPS[0]["full_description"])
        self.assertEqual(first["snapshots"], [])
        self.assertEqual(first["sort_order"], 1)


if __name__ == "__main__":
    unittest.main()
