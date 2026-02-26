import importlib
import inspect
import pkgutil
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import backend.Controllers.api as api_controllers_pkg
import backend.Controllers.web as web_controllers_pkg
from backend.Repositories.BaseRepository import BaseRepository


class ControllerSmokeTests(unittest.TestCase):
    @staticmethod
    def _controller_modules():
        for package in (api_controllers_pkg, web_controllers_pkg):
            for module_info in pkgutil.iter_modules(package.__path__):
                if module_info.ispkg:
                    continue
                yield f"{package.__name__}.{module_info.name}"

    def test_all_controller_modules_import_and_expose_callables(self):
        imported_modules = []
        callable_exports = []

        def fake_get_mongo_client(self, collection_name):
            return object(), {"name": "fake_db"}, SimpleNamespace(name=collection_name)

        with patch.object(BaseRepository, "get_mongo_client", new=fake_get_mongo_client):
            for module_path in self._controller_modules():
                module = importlib.import_module(module_path)
                imported_modules.append(module_path)

                functions = [
                    name
                    for name, fn in inspect.getmembers(module, inspect.isfunction)
                    if fn.__module__ == module.__name__ and not name.startswith("_")
                ]
                callable_exports.extend(f"{module_path}.{name}" for name in functions)

                # Every controller/support module should expose at least one public function.
                self.assertGreater(
                    len(functions),
                    0,
                    f"{module_path} does not expose public functions; if intentional, update this test.",
                )

        self.assertGreaterEqual(
            len(imported_modules),
            15,
            f"Unexpected controller module coverage: {len(imported_modules)} ({imported_modules})",
        )
        self.assertGreaterEqual(
            len(callable_exports),
            30,
            f"Unexpectedly low public controller callable coverage: {len(callable_exports)}",
        )


if __name__ == "__main__":
    unittest.main()
