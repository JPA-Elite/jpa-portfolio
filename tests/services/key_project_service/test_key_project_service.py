import unittest
from unittest.mock import MagicMock, patch

from backend.Services.KeyProjectService import KeyProjectService
from backend.configurations import SortOrder

from tests.services._service_fixtures import key_project_doc


class KeyProjectServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = KeyProjectService(repository=self.repo)

    def test_get_key_project_by_id_returns_repository_value(self):
        self.repo.get_key_project_by_id.return_value = key_project_doc()

        result = self.service.get_key_project_by_id("kp1")

        self.assertEqual(result["id"], "kp1")
        self.repo.get_key_project_by_id.assert_called_once_with("kp1")

    def test_get_paginated_key_projects_maps_models(self):
        self.repo.get_paginated_key_projects.return_value = ([key_project_doc()], 1)

        items, total = self.service.get_paginated_key_projects(1, 10, SortOrder.DESC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].id, "kp1")
        self.assertEqual(items[0].title["en"], "Project")
        self.repo.get_paginated_key_projects.assert_called_once_with(
            1,
            10,
            SortOrder.DESC,
            "",
            status_filter="",
            is_active_filter=None,
        )

    def test_get_paginated_key_projects_forwards_filters(self):
        self.repo.get_paginated_key_projects.return_value = ([key_project_doc()], 1)

        self.service.get_paginated_key_projects(
            2,
            5,
            SortOrder.ASC,
            "python",
            status_filter="planned",
            is_active_filter=False,
        )

        self.repo.get_paginated_key_projects.assert_called_once_with(
            2,
            5,
            SortOrder.ASC,
            "python",
            status_filter="planned",
            is_active_filter=False,
        )

    def test_get_active_key_projects_maps_models(self):
        self.repo.get_active_key_projects.return_value = [key_project_doc()]

        items = self.service.get_active_key_projects()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].stack, "Python")
        self.assertEqual(items[0].status, "planned")

    def test_add_key_project_without_files_saves_model(self):
        self.repo.add_key_project.return_value = "kp-new"

        result = self.service.add_key_project(
            {
                "title": {"en": "Project"},
                "description": {"en": "Desc"},
                "stack": "Python",
                "status": "planned",
                "slides_meta": [],
            }
        )

        self.assertEqual(result, "kp-new")
        saved = self.repo.add_key_project.call_args[0][0].to_dict()
        self.assertTrue(saved["id"])
        self.assertEqual(saved["image_url"], None)
        self.assertEqual(saved["slides"], [])

    def test_update_key_project_returns_false_when_missing(self):
        self.repo.get_key_project_by_id.return_value = None

        result = self.service.update_key_project("kp1", {"title": {"en": "New"}})

        self.assertFalse(result)
        self.repo.update_key_project.assert_not_called()

    def test_update_key_project_without_new_files_keeps_existing_assets(self):
        existing = key_project_doc()
        existing["slides"] = [{"id": "s1", "image_url": "/slide.jpg"}]
        self.repo.get_key_project_by_id.return_value = existing
        self.repo.update_key_project.return_value = True

        result = self.service.update_key_project(
            "kp1",
            {
                "title": {"en": "Updated"},
                "description": {"en": "Updated Desc"},
                "stack": "Python, Flask",
            },
        )

        self.assertTrue(result)
        args = self.repo.update_key_project.call_args[0]
        self.assertEqual(args[0], "kp1")
        updated = args[1].to_dict()
        self.assertEqual(updated["title"]["en"], "Updated")
        self.assertEqual(updated["stack"], "Python, Flask")
        self.assertEqual(updated["image_url"], existing["image_url"])
        self.assertEqual(updated["slides"], existing["slides"])

    def test_delete_key_project_returns_false_when_missing(self):
        self.repo.get_key_project_by_id.return_value = None

        result = self.service.delete_key_project("kp1")

        self.assertFalse(result)
        self.repo.delete_key_project.assert_not_called()

    def test_delete_key_project_cleans_cover_and_slide_images(self):
        existing = key_project_doc()
        existing["image_url"] = "https://res.cloudinary.com/demo/image/upload/cover.webp"
        existing["slides"] = [
            {"id": "s1", "image_url": "https://res.cloudinary.com/demo/image/upload/s1.webp"},
            {"id": "s2", "image_url": None},
        ]
        self.repo.get_key_project_by_id.return_value = existing
        self.repo.delete_key_project.return_value = True

        with patch.object(self.service, "_cleanup_image_url") as mock_cleanup:
            result = self.service.delete_key_project("kp1")

        self.assertTrue(result)
        self.repo.delete_key_project.assert_called_once_with("kp1")
        mock_cleanup.assert_any_call(existing["image_url"])
        mock_cleanup.assert_any_call(existing["slides"][0]["image_url"])

    def test_seed_default_projects_if_empty_returns_zero_when_existing_projects_present(self):
        self.repo.count_key_projects.return_value = 1

        result = self.service.seed_default_projects_if_empty()

        self.assertEqual(result, 0)
        self.repo.add_many_key_projects.assert_not_called()

    def test_seed_default_projects_if_empty_inserts_defaults(self):
        self.repo.count_key_projects.return_value = 0
        with patch.object(
            self.service,
            "_default_project_seed_data",
            return_value=[
                {
                    "id": "seed-1",
                    "title": {"en": "Seed"},
                    "description": {"en": "Seed Desc"},
                    "stack": "Python",
                    "status": "planned",
                    "image_url": "/seed.png",
                    "demo_url": "",
                    "repo_url": "",
                    "sort_order": 1,
                    "is_active": True,
                    "slides": [],
                }
            ],
        ):
            result = self.service.seed_default_projects_if_empty()

        self.assertEqual(result, 1)
        self.repo.add_many_key_projects.assert_called_once()
        seeded_models = self.repo.add_many_key_projects.call_args[0][0]
        self.assertEqual(len(seeded_models), 1)
        self.assertEqual(seeded_models[0].id, "seed-1")


if __name__ == "__main__":
    unittest.main()
