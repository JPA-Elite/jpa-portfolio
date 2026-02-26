import importlib
import inspect
import pkgutil
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import backend.Repositories as repositories_pkg
from backend.Repositories.BaseRepository import BaseRepository


class RepositorySmokeTests(unittest.TestCase):
    def _iter_repository_classes(self):
        package_path = repositories_pkg.__path__
        package_name = repositories_pkg.__name__
        for module_info in pkgutil.iter_modules(package_path):
            if module_info.ispkg:
                continue
            module_name = module_info.name
            if module_name in {"BaseRepository"}:
                continue
            module = importlib.import_module(f"{package_name}.{module_name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if (
                    cls.__module__ == module.__name__
                    and cls.__name__.endswith("Repository")
                    and cls.__name__ != "BaseRepository"
                ):
                    yield cls

    def test_all_repository_classes_instantiate_with_mocked_mongo(self):
        instantiated = []

        def fake_get_mongo_client(self, collection_name):
            return object(), {"name": "fake_db"}, SimpleNamespace(name=collection_name)

        with patch.object(BaseRepository, "get_mongo_client", new=fake_get_mongo_client):
            for repo_class in self._iter_repository_classes():
                repo = repo_class()
                instantiated.append(repo_class.__name__)
                self.assertTrue(hasattr(repo, "collection"))
                self.assertTrue(hasattr(repo, "db"))
                self.assertTrue(hasattr(repo, "client"))

        self.assertGreaterEqual(
            len(instantiated), 13,
            f"Expected repository coverage for all repository classes, got {len(instantiated)}: {instantiated}"
        )


if __name__ == "__main__":
    unittest.main()
