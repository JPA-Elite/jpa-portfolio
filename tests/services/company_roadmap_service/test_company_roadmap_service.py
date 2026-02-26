import unittest
from unittest.mock import MagicMock, patch

from backend.Services.CompanyRoadmapService import CompanyRoadmapService
from backend.configurations import SortOrder

from tests.services._service_fixtures import roadmap_doc


class CompanyRoadmapServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = CompanyRoadmapService(repository=self.repo)

    def test_get_company_roadmap_by_id_returns_repository_value(self):
        self.repo.get_company_roadmap_by_id.return_value = roadmap_doc()

        result = self.service.get_company_roadmap_by_id("cr1")

        self.assertEqual(result["company_name"], "Chronostep")
        self.repo.get_company_roadmap_by_id.assert_called_once_with("cr1")

    def test_get_paginated_company_roadmaps_maps_models(self):
        self.repo.get_paginated_company_roadmaps.return_value = ([roadmap_doc()], 1)

        items, total = self.service.get_paginated_company_roadmaps(1, 10, SortOrder.ASC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].company_name, "Chronostep")
        self.repo.get_paginated_company_roadmaps.assert_called_once_with(1, 10, SortOrder.ASC)

    def test_get_active_company_roadmaps_maps_models(self):
        self.repo.get_active_company_roadmaps.return_value = [roadmap_doc()]

        items = self.service.get_active_company_roadmaps()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].role_title, "Intern")
        self.repo.get_active_company_roadmaps.assert_called_once_with()

    def test_add_company_roadmap_normalizes_fields_and_saves_model(self):
        self.repo.add_company_roadmap.return_value = "new-roadmap-id"
        data = {
            "company_name": "New Co",
            "role_title": "Engineer",
            "period": "2025",
            "highlights": "One\nTwo\n",
            "accent_color": "123abc",
            "activities_meta": [],
        }

        result = self.service.add_company_roadmap(data)

        self.assertEqual(result, "new-roadmap-id")
        saved_model = self.repo.add_company_roadmap.call_args[0][0]
        saved = saved_model.to_dict()
        self.assertTrue(saved["id"])
        self.assertEqual(saved["company_name"], "New Co")
        self.assertEqual(saved["highlights"], ["One", "Two"])
        self.assertEqual(saved["accent_color"], "#123abc")
        self.assertEqual(saved["activities"], [])
        self.assertEqual(saved["role_title_i18n"]["en"], "Engineer")
        self.assertEqual(saved["definition_i18n"], None)

    def test_update_company_roadmap_returns_false_when_missing(self):
        self.repo.get_company_roadmap_by_id.return_value = None

        result = self.service.update_company_roadmap("cr1", {"summary": "Updated"})

        self.assertFalse(result)
        self.repo.update_company_roadmap.assert_not_called()

    def test_update_company_roadmap_merges_fields_and_updates_model(self):
        existing = roadmap_doc()
        existing["cover_image_url"] = "/cover.jpg"
        existing["activities"] = [{"id": "a1", "image_url": "/a1.jpg", "title": "Old", "caption": "Old"}]
        self.repo.get_company_roadmap_by_id.return_value = existing
        self.repo.update_company_roadmap.return_value = True

        result = self.service.update_company_roadmap(
            "cr1",
            {
                "summary": "Updated summary",
                "highlights": "Fresh 1\nFresh 2",
                "accent_color": "zzzz",  # invalid -> default
            },
        )

        self.assertTrue(result)
        args = self.repo.update_company_roadmap.call_args[0]
        self.assertEqual(args[0], "cr1")
        updated = args[1].to_dict()
        self.assertEqual(updated["company_name"], existing["company_name"])
        self.assertEqual(updated["summary"], "Updated summary")
        self.assertEqual(updated["highlights"], ["Fresh 1", "Fresh 2"])
        self.assertEqual(updated["accent_color"], "#2962ff")
        self.assertEqual(updated["activities"], existing["activities"])
        self.assertEqual(updated["cover_image_url"], "/cover.jpg")

    def test_delete_company_roadmap_returns_false_when_missing(self):
        self.repo.get_company_roadmap_by_id.return_value = None

        result = self.service.delete_company_roadmap("cr1")

        self.assertFalse(result)
        self.repo.delete_company_roadmap.assert_not_called()

    def test_delete_company_roadmap_cleans_images_and_deletes_record(self):
        existing = roadmap_doc()
        existing["cover_image_url"] = "https://res.cloudinary.com/demo/image/upload/cover.webp"
        existing["activities"] = [
            {"id": "a1", "image_url": "https://res.cloudinary.com/demo/image/upload/a1.webp"},
            {"id": "a2", "image_url": None},
        ]
        self.repo.get_company_roadmap_by_id.return_value = existing
        self.repo.delete_company_roadmap.return_value = True

        with patch.object(self.service, "_cleanup_image_url") as mock_cleanup:
            result = self.service.delete_company_roadmap("cr1")

        self.assertTrue(result)
        self.repo.delete_company_roadmap.assert_called_once_with("cr1")
        self.assertGreaterEqual(mock_cleanup.call_count, 2)
        mock_cleanup.assert_any_call(existing["cover_image_url"])
        mock_cleanup.assert_any_call(existing["activities"][0]["image_url"])

    def test_seed_default_company_roadmaps_if_empty_returns_zero_when_records_exist(self):
        self.repo.count_company_roadmaps.return_value = 2

        result = self.service.seed_default_company_roadmaps_if_empty()

        self.assertEqual(result, 0)
        self.repo.add_many_company_roadmaps.assert_not_called()

    def test_seed_default_company_roadmaps_if_empty_inserts_defaults(self):
        self.repo.count_company_roadmaps.return_value = 0

        result = self.service.seed_default_company_roadmaps_if_empty()

        self.assertEqual(result, 4)
        self.repo.add_many_company_roadmaps.assert_called_once()
        seeded_models = self.repo.add_many_company_roadmaps.call_args[0][0]
        self.assertEqual(len(seeded_models), 4)
        self.assertEqual(seeded_models[0].company_name, "Municipality of Vallehermoso")


if __name__ == "__main__":
    unittest.main()
