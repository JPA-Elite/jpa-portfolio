import unittest
from unittest.mock import patch

from app.Services.GeminiService import GeminiService


class _FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class GeminiServiceTests(unittest.TestCase):
    def test_unavailable_without_key(self):
        service = GeminiService(api_key="")
        self.assertFalse(service.is_available())
        self.assertIsNone(service.answer("hi", "ctx"))

    def test_returns_none_for_unrelated_marker(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="UNRELATED"):
            self.assertIsNone(service.answer("weather?", "ctx"))

    def test_returns_none_when_marker_appears_in_response(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="I cannot help. UNRELATED"):
            self.assertIsNone(service.answer("weather?", "ctx"))

    def test_returns_none_for_related_marker(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="RELATED"):
            self.assertIsNone(service.answer("weather?", "ctx"))

    def test_returns_none_for_not_related_marker(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="NOT RELATED"):
            self.assertIsNone(service.answer("weather?", "ctx"))

    def test_keeps_answer_mentioning_related_word(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="This is related to my skills."):
            result = service.answer("skills?", "ctx")
        self.assertEqual(result, "This is related to my skills.")

    def test_returns_answer_for_related_question(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="Joshua is a developer."):
            result = service.answer("who is joshua?", "ctx")
        self.assertEqual(result, "Joshua is a developer.")

    def test_returns_none_when_generate_fails(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value=None):
            self.assertIsNone(service.answer("hi", "ctx"))

    def test_returns_none_for_empty_question(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="answer"):
            self.assertIsNone(service.answer("   ", "ctx"))
        self.assertIsNone(service.answer(None, "ctx"))

    def test_build_prompt_contains_context_and_question(self):
        service = GeminiService(api_key="key")
        prompt = service._build_prompt("SITE FACTS", "who are you?")
        self.assertIn("SITE FACTS", prompt)
        self.assertIn("who are you?", prompt)
        self.assertIn("UNRELATED", prompt)

    def test_build_prompt_forces_first_person(self):
        service = GeminiService(api_key="key")
        prompt = service._build_prompt("SITE", "who are you?")
        self.assertIn("ALWAYS speak in first person", prompt)
        self.assertIn("'he', 'him'", prompt)
        self.assertIn("Never refer to Joshua by name", prompt)

    def test_build_prompt_requires_absolute_plain_urls(self):
        service = GeminiService(api_key="key")
        prompt = service._build_prompt("SITE", "give me the link")
        self.assertIn("full absolute URL", prompt)
        self.assertIn("Never use markdown link syntax or relative paths", prompt)

    def test_build_prompt_allows_company_knowledge(self):
        service = GeminiService(api_key="key")
        prompt = service._build_prompt("SITE", "what is chronostep about?")
        self.assertIn("own knowledge", prompt)
        self.assertIn("Chronostep", prompt)
        self.assertIn("do not reply with UNRELATED", prompt)

    def test_build_prompt_allows_detailed_company_answers(self):
        service = GeminiService(api_key="key")
        prompt = service._build_prompt("SITE", "tell me about your company")
        self.assertIn("thorough, detailed answer", prompt)

    def test_falls_back_when_primary_model_quota_exhausted(self):
        def fake_post(url, **kwargs):
            if "gemini-3.7-flash" in url:
                return _FakeResponse(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}})
            return _FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "fallback answer"}]}}]})

        service = GeminiService(api_key="key")
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            result = service.answer("hi", "ctx")
        self.assertEqual(result, "fallback answer")
        self.assertEqual(service._working_model, "gemini-3.6-flash")

    def test_returns_none_when_all_models_quota_exhausted(self):
        def fake_post(url, **kwargs):
            return _FakeResponse(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}})

        service = GeminiService(api_key="key")
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            result = service.answer("hi", "ctx")
        self.assertIsNone(result)

    def test_build_prompt_includes_history(self):
        service = GeminiService(api_key="key")
        prompt = service._build_prompt(
            "SITE",
            "how about in backend",
            history=[
                {"role": "user", "text": "tell me your frontend languages"},
                {"role": "bot", "text": "JavaScript, HTML, and CSS."},
            ],
        )
        self.assertIn("tell me your frontend languages", prompt)
        self.assertIn("JavaScript, HTML, and CSS.", prompt)
        self.assertIn("how about in backend", prompt)

    def test_answer_passes_history_to_prompt(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate", return_value="Backend: Python and PHP.") as generate:
            result = service.answer(
                "how about in backend",
                "SITE",
                history=[{"role": "user", "text": "frontend?"}],
            )
        self.assertEqual(result, "Backend: Python and PHP.")
        self.assertIn("frontend?", generate.call_args[0][0])

    def test_reads_multiple_keys_from_env(self):
        env = {
            "GEMINI_API_KEY": "key-one",
            "GEMINI_API_KEY_2": "key-two",
            "GEMINI_API_KEY_3": "key-three",
            "GEMINI_API_KEY_4": "key-four",
            "GEMINI_API_KEY_5": "key-five",
        }
        service = GeminiService()
        with patch.dict("os.environ", env, clear=True):
            self.assertEqual(service.api_keys, ["key-one", "key-two", "key-three", "key-four", "key-five"])

    def test_filters_blank_keys_from_env(self):
        env = {"GEMINI_API_KEY": "key-one", "GEMINI_API_KEY_2": ""}
        service = GeminiService()
        with patch.dict("os.environ", env, clear=True):
            self.assertEqual(service.api_keys, ["key-one"])

    def test_supports_unlimited_keys_from_env(self):
        env = {
            "GEMINI_API_KEY": "key-one",
            "GEMINI_API_KEY_2": "key-two",
            "GEMINI_API_KEY_3": "key-three",
            "GEMINI_API_KEY_6": "key-six",
            "GEMINI_API_KEY_7": "key-seven",
            "GEMINI_API_KEY_4": "key-four",
            "GEMINI_API_KEY_5": "key-five",
            "GEMINI_API_KEY_10": "key-ten",
            "UNRELATED_VAR": "ignored",
        }
        service = GeminiService()
        with patch.dict("os.environ", env, clear=True):
            self.assertEqual(
                service.api_keys,
                ["key-one", "key-two", "key-three", "key-four", "key-five", "key-six", "key-seven", "key-ten"],
            )

    def test_rotates_to_next_key_when_quota_exhausted(self):
        calls = []

        def fake_post(url, **kwargs):
            key = kwargs["params"]["key"]
            calls.append(key)
            if key == "key-one":
                return _FakeResponse(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}})
            return _FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "answer from key two"}]}}]})

        service = GeminiService(api_keys=["key-one", "key-two"])
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            result = service.answer("hi", "ctx")
        self.assertEqual(result, "answer from key two")
        self.assertIn("key-one", calls)
        self.assertIn("key-two", calls)
        self.assertEqual(service._working_key, "key-two")

    def test_rotates_through_all_keys_when_all_quota_exhausted(self):
        keys_tried = []

        def fake_post(url, **kwargs):
            keys_tried.append(kwargs["params"]["key"])
            return _FakeResponse(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}})

        service = GeminiService(api_keys=["k1", "k2", "k3", "k4", "k5"])
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            result = service.answer("hi", "ctx")
        self.assertIsNone(result)
        self.assertEqual(set(keys_tried), {"k1", "k2", "k3", "k4", "k5"})

    def test_rotates_through_seven_keys_when_all_quota_exhausted(self):
        keys_tried = []

        def fake_post(url, **kwargs):
            keys_tried.append(kwargs["params"]["key"])
            return _FakeResponse(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}})

        service = GeminiService(api_keys=[f"k{i}" for i in range(1, 8)])
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            result = service.answer("hi", "ctx")
        self.assertIsNone(result)
        self.assertEqual(set(keys_tried), {f"k{i}" for i in range(1, 8)})

    def test_prefers_working_key_on_subsequent_calls(self):
        def fake_post(url, **kwargs):
            key = kwargs["params"]["key"]
            if key == "key-one":
                return _FakeResponse(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}})
            return _FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

        service = GeminiService(api_keys=["key-one", "key-two"])
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            self.assertEqual(service.answer("first", "ctx"), "ok")
            self.assertEqual(service._working_key, "key-two")
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post) as post:
            self.assertEqual(service.answer("second", "ctx"), "ok")
            first_key = post.call_args_list[0][1]["params"]["key"]
        self.assertEqual(first_key, "key-two")

    def test_skips_exhausted_combo_on_retry(self):
        calls = []

        def fake_post(url, **kwargs):
            key = kwargs["params"]["key"]
            model = url.rsplit("/", 1)[-1]
            calls.append((key, model))
            return _FakeResponse(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}})

        service = GeminiService(api_keys=["k1", "k2"])
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            self.assertIsNone(service.answer("first", "ctx"))
            first_call_count = len(calls)
            self.assertEqual(first_call_count, 10)
            self.assertIsNone(service.answer("second", "ctx"))
        self.assertEqual(len(calls), first_call_count)
        self.assertEqual(set(calls), {("k1", m) for m in ["gemini-3.7-flash:generateContent", "gemini-3.6-flash:generateContent", "gemini-3.5-flash:generateContent", "gemini-3.5-flash-lite:generateContent", "gemini-3.1-flash-lite:generateContent"]} | {("k2", m) for m in ["gemini-3.7-flash:generateContent", "gemini-3.6-flash:generateContent", "gemini-3.5-flash:generateContent", "gemini-3.5-flash-lite:generateContent", "gemini-3.1-flash-lite:generateContent"]})
