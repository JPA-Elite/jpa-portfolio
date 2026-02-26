import unittest

from tests.services._service_methods_test_helpers import run_service_methods_test


class VisitServiceMethodExecutionTests(unittest.TestCase):
    def test_all_public_methods_execute(self):
        run_service_methods_test(self, "VisitService", "VisitService")


if __name__ == "__main__":
    unittest.main()
