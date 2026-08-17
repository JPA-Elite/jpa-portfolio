import unittest
from contextlib import ExitStack
from unittest.mock import patch

from flask import Flask, Response

from app.Repositories.BaseRepository import BaseRepository
from tests.controllers.shared._controller_test_helpers import _fake_get_mongo_client, _patch_module_dependencies


class ProfileConfigLocalizationTests(unittest.TestCase):
    def _module(self, stack):
        stack.enter_context(patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client))
        import app.Controllers.api.BaseController as base_controller

        _patch_module_dependencies(stack, base_controller)
        return base_controller

    def _localized_qa(self, locale):
        app = Flask(__name__)
        app.secret_key = "test-secret"
        with ExitStack() as stack:
            module = self._module(stack)
            module.chat_service.get_qa_data.return_value = [
                {"question": "Unsa ang imong pangalan?", "answer": "Si Joshua ko."}
                if locale == "ceb"
                else {"question": "Ano ang pangalan mo?", "answer": "Si Joshua ako."}
            ]
            with app.test_request_context("/api/profile-config"):
                module.request.cookies = {"lang": locale}
                response = module.profile_config_route()
        return response

    def test_profile_config_localizes_cebuano(self):
        response = self._localized_qa("ceb")
        data = response.get_json()
        self.assertEqual(data["qaData"][0]["question"], "Unsa ang imong pangalan?")

    def test_profile_config_localizes_tagalog(self):
        response = self._localized_qa("fil_PH")
        data = response.get_json()
        self.assertEqual(data["qaData"][0]["question"], "Ano ang pangalan mo?")

    def test_profile_config_sets_no_store_header(self):
        response = self._localized_qa("en")
        self.assertIsInstance(response, Response)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")


if __name__ == "__main__":
    unittest.main()
