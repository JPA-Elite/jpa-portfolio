import unittest
from unittest.mock import MagicMock

from backend.Services.CompanyRoadmapService import CompanyRoadmapService


class CompanyRoadmapServiceI18nTests(unittest.TestCase):
    def setUp(self):
        self.service = CompanyRoadmapService(repository=MagicMock())

    def test_normalize_i18n_text_map_uses_english_fallback(self):
        result = self.service._normalize_i18n_text_map({"ceb": "Sugilanon"}, "Story")
        self.assertEqual(result["en"], "Story")
        self.assertEqual(result["ceb"], "Sugilanon")
        self.assertEqual(result["fil_PH"], "")

    def test_normalize_i18n_highlights_map_supports_multiline_strings(self):
        result = self.service._normalize_i18n_highlights_map(
            {"en": "Line 1\nLine 2", "ceb": "Usa\nDuha"},
            None,
        )
        self.assertEqual(result["en"], ["Line 1", "Line 2"])
        self.assertEqual(result["ceb"], ["Usa", "Duha"])
        self.assertEqual(result["fil_PH"], [])

    def test_merge_i18n_text_map_preserves_existing_translations(self):
        merged = self.service._merge_i18n_text_map(
            {"en": "Developer", "ceb": "Developer", "fil_PH": "Developer"},
            {"ceb": "Tighimo og software", "fil_PH": "Developer ng software"},
            "Developer",
            "Developer",
        )
        self.assertEqual(merged["en"], "Developer")
        self.assertEqual(merged["ceb"], "Tighimo og software")
        self.assertEqual(merged["fil_PH"], "Developer ng software")

    def test_merge_i18n_highlights_map_updates_english_when_provided(self):
        merged = self.service._merge_i18n_highlights_map(
            {"en": ["Old"], "ceb": ["Daan"], "fil_PH": []},
            {"ceb": ["Bag-o"], "fil_PH": ["Bago"]},
            "New\nList",
            ["Old"],
        )
        self.assertEqual(merged["en"], ["New", "List"])
        self.assertEqual(merged["ceb"], ["Bag-o"])
        self.assertEqual(merged["fil_PH"], ["Bago"])


if __name__ == "__main__":
    unittest.main()

