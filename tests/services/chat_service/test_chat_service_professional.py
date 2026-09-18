import os
import unittest
from unittest.mock import patch

from app.Services.ChatService import (
    ChatService,
    PROFESSIONAL_QUESTION_HEADINGS,
    PROFESSIONAL_QUESTION_HEADINGS,
)

from tests.services._service_fixtures import build_test_app


class ChatServiceProfessionalTests(unittest.TestCase):
    def setUp(self):
        self.app = build_test_app()
        self._env_patcher = patch.dict(os.environ, {
            "LANDING_DOMAIN": "jpastack.local",
            "PROFESSIONAL_DOMAIN": "professional.jpastack.local",
            "SOCIAL_DOMAIN": "social.jpastack.local",
            "ADMIN_DOMAIN": "config.jpastack.local",
        })
        self._env_patcher.start()
        self.addCleanup(self._env_patcher.stop)

    def _service(self):
        return ChatService()

    def test_professional_host_returns_only_professional_questions(self):
        service = self._service()
        with self.app.test_request_context("/", base_url="http://professional.jpastack.local"):
            self.assertTrue(service._is_professional_site())
            items = service.get_qa_data()
        self.assertTrue(len(items) > 0)
        for item in items:
            self.assertIn(item["source_heading"], PROFESSIONAL_QUESTION_HEADINGS)
        headings = [item["source_heading"] for item in items]
        self.assertIn("Skills", headings)
        self.assertNotIn("Concern", headings)
        self.assertNotIn("What kind of songs do you like?", headings)
        self.assertNotIn("Who is your crush?", headings)

    def test_professional_subset_is_smaller_than_full_guide(self):
        from app.Services.KnowledgeBaseService import KnowledgeBaseService

        service = self._service()
        with self.app.test_request_context("/", base_url="http://professional.jpastack.local"):
            work_items = service.get_qa_data()
        total_sections = len(KnowledgeBaseService().sections())
        self.assertTrue(0 < len(work_items) < total_sections)

    def test_social_host_returns_full_question_list(self):
        service = self._service()
        with self.app.test_request_context("/", base_url="http://jpastack.local"):
            self.assertFalse(service._is_professional_site())
            items = service.get_qa_data()
        headings = [item["source_heading"] for item in items]
        self.assertIn("Skills", headings)
        self.assertIn("What kind of songs do you like?", headings)
        self.assertIn("Who is your crush?", headings)
        self.assertFalse(any("display_question" in item for item in items))

    def test_no_request_context_returns_full_question_list(self):
        service = self._service()
        self.assertFalse(service._is_professional_site())
        items = service.get_qa_data()
        self.assertTrue(len(items) > 0)
        headings = [item["source_heading"] for item in items]
        self.assertIn("What kind of songs do you like?", headings)

    def test_ai_context_is_professional_on_professional_host(self):
        service = self._service()
        with self.app.test_request_context("/", base_url="http://professional.jpastack.local"):
            context = service._ai_context()
        self.assertIn("SITE MODE: professional", context)
        self.assertIn("https://forms.gle/5UqVgzzxgkJS11Qj9", context)

    def test_ai_context_is_social_on_social_host(self):
        service = self._service()
        with self.app.test_request_context("/", base_url="http://social.jpastack.local"):
            context = service._ai_context()
        self.assertIn("SITE MODE: social", context)

    def test_quick_questions_reply_uses_professional_subset(self):
        service = self._service()
        with self.app.test_request_context("/", base_url="http://professional.jpastack.local"):
            with patch("app.Services.ChatService.gettext", side_effect=lambda key: key):
                result = service.resolve("show me quick questions")
        self.assertIn("What are your skills?", result["answer"])
        self.assertNotIn("What kind of songs do you like?", result["answer"])

    def test_professional_labels_start_with_question_word_and_end_with_mark(self):
        from app.Services.ChatService import QUESTION_STARTERS

        service = self._service()
        with self.app.test_request_context("/", base_url="http://professional.jpastack.local"):
            items = service.get_qa_data()
        self.assertTrue(len(items) > 0)
        for item in items:
            label = item.get("display_question") or ""
            self.assertTrue(label.endswith("?"), f"missing question mark: {label!r}")
            first_word = label.split(" ")[0].lower()
            self.assertIn(first_word, QUESTION_STARTERS, f"bad starter: {label!r}")

    def test_professional_labels_keep_canonical_matchable_question(self):
        service = self._service()
        with self.app.test_request_context("/", base_url="http://professional.jpastack.local"):
            items = service.get_qa_data()
        by_label = {item.get("display_question"): item.get("question") for item in items}
        self.assertEqual(by_label.get("What are your skills?"), "Skills")
        self.assertEqual(by_label.get("How can I contact you?"), "Contact")
        self.assertEqual(by_label.get("How do I book your services?"), "Booking")


if __name__ == "__main__":
    unittest.main()
