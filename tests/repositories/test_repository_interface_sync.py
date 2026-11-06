import importlib
import inspect
import pathlib
import unittest
from abc import ABC

from app.Repositories.BaseRepository import BaseRepository


REPOSITORY_DIR = pathlib.Path(__file__).resolve().parents[2] / "app" / "Repositories"


def _repository_classes():
    for path in sorted(REPOSITORY_DIR.glob("*.py")):
        if path.name.startswith("_") or path.name == "BaseRepository.py":
            continue
        module = importlib.import_module(f"app.Repositories.{path.stem}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls is BaseRepository or cls.__module__ != module.__name__:
                continue
            if not issubclass(cls, BaseRepository):
                continue
            yield cls


def _interface_of(cls):
    for base in cls.__bases__:
        if base is not BaseRepository and issubclass(base, ABC):
            return base
    return None


def _public_methods(cls):
    return {
        name: fn
        for name, fn in inspect.getmembers(cls, inspect.isfunction)
        if fn.__module__ == cls.__module__ and not name.startswith("_")
    }


def _signature_shape(fn):
    return [
        (parameter.name, parameter.kind, parameter.default)
        for parameter in inspect.signature(fn).parameters.values()
    ]


class RepositoryInterfaceSyncTests(unittest.TestCase):
    def test_every_repository_has_a_matching_interface(self):
        for cls in _repository_classes():
            with self.subTest(repository=cls.__name__):
                interface = _interface_of(cls)
                self.assertIsNotNone(interface, f"{cls.__name__} has no abstract interface")
                self.assertEqual(interface.__name__, f"I{cls.__name__}")

    def test_every_abstract_method_is_implemented(self):
        for cls in _repository_classes():
            interface = _interface_of(cls)
            if interface is None:
                continue
            for method_name in getattr(interface, "__abstractmethods__", set()):
                with self.subTest(repository=cls.__name__, method=method_name):
                    method = getattr(cls, method_name, None)
                    self.assertTrue(callable(method), f"{cls.__name__} does not implement {method_name}")
                    self.assertFalse(getattr(method, "__isabstractmethod__", False))

    def test_repository_public_methods_are_declared_in_the_interface(self):
        for cls in _repository_classes():
            interface = _interface_of(cls)
            if interface is None:
                continue
            declared = {
                name
                for name, _ in inspect.getmembers(interface, inspect.isfunction)
                if not name.startswith("_")
            }
            missing = sorted(set(_public_methods(cls)) - declared)
            with self.subTest(repository=cls.__name__):
                self.assertEqual(
                    missing,
                    [],
                    f"{cls.__name__} methods missing from {interface.__name__}: {missing}",
                )

    def test_interface_and_repository_signatures_match(self):
        for cls in _repository_classes():
            interface = _interface_of(cls)
            if interface is None:
                continue
            for method_name in getattr(interface, "__abstractmethods__", set()):
                with self.subTest(repository=cls.__name__, method=method_name):
                    self.assertEqual(
                        _signature_shape(getattr(interface, method_name)),
                        _signature_shape(getattr(cls, method_name)),
                        f"{cls.__name__}.{method_name} signature differs from {interface.__name__}",
                    )


if __name__ == "__main__":
    unittest.main()
