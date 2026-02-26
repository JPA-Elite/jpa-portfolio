import unittest

from tests.services._service_methods_test_helpers import run_service_methods_test


class CompanyRoadmapServiceMethodExecutionTests(unittest.TestCase):
    def test_all_public_methods_execute(self):
        run_service_methods_test(self, "CompanyRoadmapService", "CompanyRoadmapService")


if __name__ == "__main__":
    unittest.main()
