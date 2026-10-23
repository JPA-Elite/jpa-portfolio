import unittest

from app.Services.PortfolioDisplayService import (
    localized_roadmap_employment_type,
    resolve_built_app_display,
    resolve_project_stack_display,
)


class PortfolioDisplayServiceTests(unittest.TestCase):
    def test_localized_roadmap_employment_type_maps_known_values(self):
        translate = lambda key: f"translated:{key}"

        self.assertEqual(
            localized_roadmap_employment_type("internship", translate),
            "translated:Career_Roadmap_Employment_Internship",
        )
        self.assertEqual(
            localized_roadmap_employment_type("full-time", translate),
            "translated:Career_Roadmap_Employment_Full_Time",
        )
        self.assertEqual(
            localized_roadmap_employment_type("Full Time", translate),
            "translated:Career_Roadmap_Employment_Full_Time",
        )
        self.assertEqual(
            localized_roadmap_employment_type("contract", translate),
            "translated:Career_Roadmap_Employment_Contract",
        )
        self.assertEqual(
            localized_roadmap_employment_type("freelance", translate),
            "translated:Career_Roadmap_Employment_Freelance",
        )
        self.assertEqual(
            localized_roadmap_employment_type("experience", translate),
            "translated:Career_Roadmap_Employment_Experience",
        )

    def test_localized_roadmap_employment_type_keeps_unknown_and_empty_values(self):
        translate = lambda key: f"translated:{key}"

        self.assertEqual(
            localized_roadmap_employment_type("Apprenticeship", translate),
            "Apprenticeship",
        )
        self.assertEqual(localized_roadmap_employment_type("", translate), "")
        self.assertEqual(localized_roadmap_employment_type(None, translate), "")

    def test_resolve_project_stack_display_localizes_dict_value(self):
        stack = {"en": "Python", "ceb": "Python Cebuano"}

        self.assertEqual(resolve_project_stack_display(stack, "ceb"), "Python Cebuano")
        self.assertEqual(resolve_project_stack_display(stack, "fr"), "Python")
        self.assertEqual(resolve_project_stack_display(stack, "fil_PH"), "Python")

    def test_resolve_project_stack_display_uses_seed_map_for_english_value(self):
        seed = {"en": "Python", "ceb": "Python Cebuano"}

        self.assertEqual(
            resolve_project_stack_display("Python", "ceb", seed),
            "Python Cebuano",
        )
        self.assertEqual(
            resolve_project_stack_display("", "ceb", seed),
            "Python Cebuano",
        )

    def test_resolve_project_stack_display_preserves_custom_value(self):
        seed = {"en": "Python", "ceb": "Python Cebuano"}

        self.assertEqual(
            resolve_project_stack_display("Rust", "ceb", seed),
            "Rust",
        )
        self.assertEqual(resolve_project_stack_display("Rust", "ceb"), "Rust")

    def test_resolve_project_stack_display_handles_missing_values(self):
        self.assertEqual(resolve_project_stack_display(None, "en"), "")
        self.assertEqual(resolve_project_stack_display({}, "ceb"), "")
        self.assertEqual(
            resolve_project_stack_display({}, "ceb", {"en": "Fallback"}),
            "Fallback",
        )

    def test_resolve_built_app_display_localizes_and_strips_fields(self):
        app = {
            "name": {"en": "TaskFlow", "fr": " Flux "},
            "short_description": {"en": "Short", "fr": " Court "},
            "full_description": {"en": ["One", " ", "Two"], "fr": [" Un "]},
            "snapshots": [
                {"id": "s1", "image_url": "/one.jpg"},
                {"id": "s2", "image_url": ""},
                "invalid",
                {"id": "s3", "image_url": "/three.jpg", "sort_order": 3},
            ],
        }

        result = resolve_built_app_display(app, "fr")

        self.assertIsNot(result, app)
        self.assertEqual(result["name"], "Flux")
        self.assertEqual(result["short_description"], "Court")
        self.assertEqual(result["full_description"], ["Un"])
        self.assertEqual(
            result["snapshots"],
            [
                {"id": "s1", "image_url": "/one.jpg", "sort_order": 0},
                {"id": "s3", "image_url": "/three.jpg", "sort_order": 3},
            ],
        )
        self.assertEqual(app["name"]["fr"], " Flux ")

    def test_resolve_built_app_display_falls_back_to_english(self):
        app = {
            "name": {"en": "TaskFlow"},
            "short_description": {"en": "Short"},
            "full_description": {"en": ["One"]},
            "snapshots": [],
        }

        result = resolve_built_app_display(app, "ceb")

        self.assertEqual(result["name"], "TaskFlow")
        self.assertEqual(result["short_description"], "Short")
        self.assertEqual(result["full_description"], ["One"])
        self.assertEqual(result["snapshots"], [])

    def test_resolve_built_app_display_handles_missing_maps(self):
        result = resolve_built_app_display({}, "en")

        self.assertEqual(result["name"], "")
        self.assertEqual(result["short_description"], "")
        self.assertEqual(result["full_description"], [])
        self.assertEqual(result["snapshots"], [])


if __name__ == "__main__":
    unittest.main()
