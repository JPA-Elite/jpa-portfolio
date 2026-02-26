import unittest

from tests.services._service_methods_test_helpers import run_service_methods_test


class VlogCommentServiceMethodExecutionTests(unittest.TestCase):
    def test_all_public_methods_execute(self):
        run_service_methods_test(self, "VlogCommentService", "VlogCommentService")


if __name__ == "__main__":
    unittest.main()
