import unittest
from unittest.mock import patch

from app.Services.ChatService import ChatService, PROFESSIONAL_QUESTION_HEADINGS

from tests.services._service_fixtures import build_test_app


class ChatServiceRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.app = build_test_app()
        self._gettext_patcher = patch(
            "app.Services.ChatService.gettext", side_effect=lambda key: key
        )
        self._gettext_patcher.start()
        self.addCleanup(self._gettext_patcher.stop)
        self._locale_patcher = patch(
            "app.Services.ChatService.get_locale", return_value="en"
        )
        self._locale_patcher.start()
        self.addCleanup(self._locale_patcher.stop)
        self._gemini_patcher = patch(
            "app.Services.ChatService.ChatService._get_gemini_service",
            new=lambda self: None,
        )
        self._gemini_patcher.start()
        self.addCleanup(self._gemini_patcher.stop)

    def _resolve(self, message, session_id="recovery"):
        service = ChatService()
        with self.app.test_request_context("/"):
            return service.resolve(message, session_id=session_id)

    def test_parttime_why_beats_company_keyword_hijack(self):
        result = self._resolve(
            "if you arre currently working in chronostep, why you need part time job"
        )
        self.assertIn("part-time", result["answer"])
        self.assertIn("Booking", result["answer"])
        self.assertNotIn("Intern @", result["answer"])

    def test_parttime_rephrase_answers_same_intent(self):
        result = self._resolve("what im said why you need to work as part time job")
        self.assertIn("part-time", result["answer"])
        self.assertIn("Chronostep", result["answer"])

    def test_side_job_maps_to_parttime_answer(self):
        result = self._resolve("do you take side jobs for extra income")
        self.assertIn("part-time", result["answer"])

    def test_parttime_section_is_a_professional_question(self):
        self.assertIn(
            "Are you open to part-time work?", PROFESSIONAL_QUESTION_HEADINGS
        )

    def test_bare_asking_complaint_redirects_to_rephrase(self):
        result = self._resolve("im asking the question")
        self.assertEqual(result["answer"], "chat_redirect_reply")
        self.assertEqual(result["action"], "expand_options")

    def test_answer_me_complaint_redirects_to_rephrase(self):
        result = self._resolve("answer my question about pricing")
        self.assertEqual(result["answer"], "chat_redirect_reply")
        self.assertEqual(result["action"], "expand_options")

    def test_job_question_still_answers_job(self):
        result = self._resolve("What is your job?")
        self.assertIn("Chronostep", result["answer"])

    def test_quick_questions_still_win_over_complaint(self):
        result = self._resolve("what can you answer")
        self.assertNotEqual(result["answer"], "chat_redirect_reply")


if __name__ == "__main__":
    unittest.main()
