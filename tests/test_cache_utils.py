import unittest

from flask import Flask

from app.extensions import cache
from app.utils import clear_cache_by_prefix


class ClearCacheByPrefixTests(unittest.TestCase):
    def _init_cache(self, cache_type):
        app = Flask(__name__)
        app.config["CACHE_TYPE"] = cache_type
        app.config["CACHE_DEFAULT_TIMEOUT"] = 60
        cache.init_app(app)
        self.addCleanup(cache.init_app, self._neutral_app())
        return app

    def _neutral_app(self):
        app = Flask(__name__)
        app.config["CACHE_TYPE"] = "simple"
        app.config["CACHE_DEFAULT_TIMEOUT"] = 60
        return app

    def test_simple_cache_deletes_only_matching_keys(self):
        app = self._init_cache("simple")
        with app.app_context():
            cache.set("admin.api.login_attempt_list:page=1", {"ok": True})
            cache.set("admin.api.login_attempt_list:page=2", {"ok": True})
            cache.set("gallery_en_", ["data"])
            clear_cache_by_prefix("admin.api.login_attempt_list:")
            self.assertIsNone(cache.get("admin.api.login_attempt_list:page=1"))
            self.assertIsNone(cache.get("admin.api.login_attempt_list:page=2"))
            self.assertEqual(cache.get("gallery_en_"), ["data"])

    def test_null_cache_never_raises(self):
        app = self._init_cache("null")
        with app.app_context():
            try:
                clear_cache_by_prefix("admin.api.login_attempt_list:")
            except Exception as exc:
                self.fail(f"clear_cache_by_prefix raised {exc!r} on NullCache")

    def test_backend_without_key_store_falls_back_to_clear(self):
        app = self._init_cache("simple")
        calls = []
        with app.app_context():
            backend = cache.cache
            original_clear = backend.clear
            original_store = backend._cache

            def spy_clear():
                calls.append("clear")
                return original_clear()

            backend.clear = spy_clear
            del backend._cache
            try:
                try:
                    clear_cache_by_prefix("admin.api.login_attempt_list:")
                except Exception as exc:
                    self.fail(f"clear_cache_by_prefix raised {exc!r} without key store")
            finally:
                backend._cache = original_store
                del backend.clear
        self.assertEqual(calls, ["clear"])


if __name__ == "__main__":
    unittest.main()
