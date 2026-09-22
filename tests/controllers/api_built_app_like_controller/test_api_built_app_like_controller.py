import unittest

from tests.controllers.shared._controller_test_helpers import (
    run_controller_module_functions_test,
)


class ApiBuiltAppLikeControllerModuleTests(unittest.TestCase):
    def test_module_import_and_public_functions(self):
        run_controller_module_functions_test(
            self, "app.Controllers.api.BuiltAppLikeController"
        )


if __name__ == "__main__":
    unittest.main()
