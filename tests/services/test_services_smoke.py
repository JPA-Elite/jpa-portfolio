import importlib
import inspect
import pkgutil
import unittest
from unittest.mock import MagicMock

import backend.Services as services_pkg


class ServiceSmokeTests(unittest.TestCase):
    def _iter_service_classes(self):
        package_path = services_pkg.__path__
        package_name = services_pkg.__name__
        for module_info in pkgutil.iter_modules(package_path):
            if module_info.ispkg:
                continue
            module = importlib.import_module(f"{package_name}.{module_info.name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ == module.__name__ and cls.__name__.endswith("Service"):
                    yield cls

    def test_all_service_classes_instantiate_with_mock_dependencies(self):
        instantiated = []

        for service_class in self._iter_service_classes():
            sig = inspect.signature(service_class.__init__)
            required_args = []
            for name, param in list(sig.parameters.items())[1:]:  # skip self
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                if param.default is inspect._empty:
                    required_args.append(MagicMock(name=f"{service_class.__name__}_{name}"))

            service = service_class(*required_args)
            instantiated.append(service_class.__name__)
            self.assertIsNotNone(service)

        self.assertGreaterEqual(
            len(instantiated), 13,
            f"Expected service coverage for all service classes, got {len(instantiated)}: {instantiated}"
        )


if __name__ == "__main__":
    unittest.main()
