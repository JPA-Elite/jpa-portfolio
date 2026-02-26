import importlib
import inspect
import pkgutil
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

import backend.Repositories as repositories_pkg
from backend.Repositories.BaseRepository import BaseRepository

from tests.test_support import FakeCollection, dummy_repo_param


class RepositoryMethodInvocationTests(unittest.TestCase):
    @staticmethod
    def _repository_classes():
        for module_info in pkgutil.iter_modules(repositories_pkg.__path__):
            if module_info.ispkg or module_info.name == "BaseRepository":
                continue
            module = importlib.import_module(f"{repositories_pkg.__name__}.{module_info.name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if (
                    cls.__module__ == module.__name__
                    and cls.__name__.endswith("Repository")
                    and cls.__name__ != "BaseRepository"
                ):
                    yield cls

    @staticmethod
    def _repo_methods(repo_class):
        for name, fn in inspect.getmembers(repo_class, inspect.isfunction):
            if fn.__module__ != repo_class.__module__:
                continue
            if name in {"__init__", "get_mongo_client"}:
                continue
            yield name, fn

    def test_all_repository_methods_execute_with_fake_collection(self):
        app = Flask(__name__)

        def fake_get_mongo_client(self, collection_name):
            return object(), {}, FakeCollection()

        executed = []
        failures = []

        with ExitStack() as stack:
            stack.enter_context(patch.object(BaseRepository, "get_mongo_client", new=fake_get_mongo_client))
            stack.enter_context(patch("backend.Repositories.LoginAttemptRepository.get_request_ip", return_value="127.0.0.1"))

            for repo_class in self._repository_classes():
                repo = repo_class()
                for method_name, method in self._repo_methods(repo_class):
                    sig = inspect.signature(method)
                    args = []
                    for param_name, param in list(sig.parameters.items())[1:]:  # skip self
                        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                            continue
                        if param.default is not inspect._empty:
                            # Use default where possible for more natural coverage.
                            continue
                        args.append(dummy_repo_param(param_name))

                    try:
                        with app.test_request_context("/"):
                            getattr(repo, method_name)(*args)
                        executed.append(f"{repo_class.__name__}.{method_name}")
                    except Exception as exc:
                        failures.append(f"{repo_class.__name__}.{method_name}: {exc}")

        if failures:
            self.fail("Repository method execution failures:\n" + "\n".join(failures))

        # Guardrail: if methods are added, this count should rise and the test will remind us to validate coverage.
        self.assertGreaterEqual(len(executed), 70, f"Unexpectedly low repository method coverage: {len(executed)}")


if __name__ == "__main__":
    unittest.main()

