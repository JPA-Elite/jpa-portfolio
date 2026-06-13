import unittest

from tests.controllers.shared._controller_test_helpers import (
    run_controller_module_functions_test,
    run_controller_module_smoke_test,
)


class ApiVideoControllerModuleTests(unittest.TestCase):
    def test_module_import_and_public_functions(self):
        run_controller_module_smoke_test(self, "app.Controllers.api.VideoController")

    def test_all_public_functions_execute(self):
        run_controller_module_functions_test(self, "app.Controllers.api.VideoController")


if __name__ == "__main__":
    unittest.main()
