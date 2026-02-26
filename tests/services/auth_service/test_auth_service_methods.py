import unittest

from tests.services._service_methods_test_helpers import run_service_methods_test


class AuthServiceMethodExecutionTests(unittest.TestCase):
    def test_all_public_methods_execute(self):
        run_service_methods_test(self, "AuthService", "AuthService")


if __name__ == "__main__":
    unittest.main()
