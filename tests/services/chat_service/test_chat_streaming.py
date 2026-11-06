import unittest
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from flask import Flask

from app.Repositories.BaseRepository import BaseRepository
from app.Services.ChatService import ChatService
from app.Services.GeminiService import GeminiService
from tests.controllers.shared._controller_test_helpers import (
    _fake_get_mongo_client,
    _patch_module_dependencies,
)


def _fake_gettext(key, *args, **kwargs):
    return key


class _FakeStreamResponse:
    def __init__(self, status_code, lines):
        self.status_code = status_code
        self._lines = lines
        self.closed = False

    def iter_lines(self, decode_unicode=False):
        for line in self._lines:
            yield line

    def close(self):
        self.closed = True


def _sse_line(text):
    return 'data: {"candidates": [{"content": {"parts": [{"text": "%s"}]}}]}' % text


class GeminiStreamingTests(unittest.TestCase):
    def test_stream_answer_yields_text_chunks(self):
        service = GeminiService(api_key="key")
        with patch.object(
            service,
            "_generate_stream",
            return_value=iter(["I build web apps. ", "Ask me anything."]),
        ):
            chunks = list(service.stream_answer("what do you do?", "ctx"))
        self.assertEqual(chunks, ["I build web apps. ", "Ask me anything."])

    def test_stream_answer_holds_short_prefix_to_check_marker(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate_stream", return_value=iter(["Hi ", "there", ", friend."])):
            chunks = list(service.stream_answer("hi", "ctx"))
        self.assertEqual(chunks, ["Hi there, friend."])

    def test_stream_answer_suppresses_unrelated_marker(self):
        service = GeminiService(api_key="key")
        with patch.object(service, "_generate_stream", return_value=iter(["UNREL", "ATED"])):
            chunks = list(service.stream_answer("weather?", "ctx"))
        self.assertEqual(chunks, [])

    def test_stream_answer_returns_nothing_without_keys(self):
        service = GeminiService(api_key="")
        self.assertEqual(list(service.stream_answer("hi", "ctx")), [])

    def test_iter_sse_text_parses_data_lines_and_skips_done(self):
        service = GeminiService(api_key="key")
        response = _FakeStreamResponse(
            200,
            ["", _sse_line("Hello "), "data: [DONE]", _sse_line("world")],
        )
        self.assertEqual(list(service._iter_sse_text(response)), ["Hello ", "world"])

    def test_generate_stream_falls_back_to_next_model(self):
        first = _FakeStreamResponse(429, [])
        second = _FakeStreamResponse(200, [_sse_line("fallback stream")])

        def fake_post(url, **kwargs):
            if "gemini-3.7-flash" in url:
                return first
            self.assertEqual(kwargs["params"]["alt"], "sse")
            self.assertTrue(kwargs["stream"])
            return second

        service = GeminiService(api_key="key")
        with patch("app.Services.GeminiService.requests.post", side_effect=fake_post):
            chunks = list(service.stream_answer("hi", "ctx"))
        self.assertEqual(chunks, ["fallback stream"])
        self.assertEqual(service._working_model, "gemini-3.6-flash")
        self.assertTrue(second.closed)


class ChatServiceStreamingTests(unittest.TestCase):
    def _stream(self, message, gemini=None):
        service = ChatService(gemini_service=gemini)
        with patch("app.Services.ChatService.gettext", side_effect=_fake_gettext), \
             patch("app.Services.ChatService.ChatService._get_gemini_service", new=lambda self: self.gemini_service):
            return list(service.resolve_stream(message))

    def test_streams_ai_tokens_and_final_answer(self):
        gemini = MagicMock()
        gemini.stream_answer.return_value = iter(["I am ", "Joshua."])
        events = self._stream("what is your name?", gemini=gemini)
        tokens = [event["text"] for event in events if event["type"] == "token"]
        final = [event for event in events if event["type"] == "final"][0]
        self.assertEqual(tokens, ["I am ", "Joshua."])
        self.assertEqual(final["result"]["answer"], "I am Joshua.")
        gemini.stream_answer.assert_called_once()
        gemini.answer.assert_not_called()

    def test_stream_falls_back_to_local_rules_when_ai_is_empty(self):
        gemini = MagicMock()
        gemini.stream_answer.return_value = iter([])
        events = self._stream("what is your name?", gemini=gemini)
        self.assertEqual([event["type"] for event in events], ["final"])
        self.assertTrue(events[0]["result"]["answer"])

    def test_stream_replies_without_tokens_for_greeting(self):
        events = self._stream("hello there")
        self.assertEqual([event["type"] for event in events], ["final"])
        self.assertEqual(events[0]["result"]["answer"], "chat_greeting_fallback")

    def test_stream_uses_answer_when_service_cannot_stream(self):
        gemini = MagicMock(spec=["answer"])
        gemini.answer.return_value = "Non streaming answer."
        events = self._stream("what are joshua's pets?", gemini=gemini)
        tokens = [event["text"] for event in events if event["type"] == "token"]
        self.assertEqual(tokens, ["Non streaming answer."])
        self.assertEqual(events[-1]["result"]["answer"], "Non streaming answer.")


class ChatStreamRouteTests(unittest.TestCase):
    def _module(self, stack):
        stack.enter_context(patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client))
        import app.Controllers.api.BaseController as base_controller

        _patch_module_dependencies(stack, base_controller)
        return base_controller

    def test_route_streams_sse_events(self):
        app = Flask(__name__)
        app.secret_key = "test-secret"
        with ExitStack() as stack:
            module = self._module(stack)
            fake_service = MagicMock()
            fake_service.resolve_stream.return_value = iter([
                {"type": "token", "text": "Hi "},
                {"type": "final", "result": {"answer": "Hi there", "action": None, "matched_question": None}},
            ])
            stack.enter_context(patch.object(module, "chat_service", fake_service))
            fake_form = MagicMock()
            fake_form.validated.return_value = ({"message": "hello", "session_id": None}, None, None)
            stack.enter_context(patch.object(module, "BaseControllerRequest", return_value=fake_form))

            with app.test_request_context("/api/chat/stream", method="POST"):
                response = module.chat_stream_route()
                body = response.get_data(as_text=True)

        self.assertEqual(response.mimetype, "text/event-stream")
        self.assertEqual(response.headers.get("X-Accel-Buffering"), "no")
        self.assertIn('"type": "start"', body)
        self.assertIn('"type": "token"', body)
        self.assertIn('"answer": "Hi there"', body)
        self.assertIn("[DONE]", body)


if __name__ == "__main__":
    unittest.main()
