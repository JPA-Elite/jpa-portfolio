import unittest

from tests.repositories.shared._repository_test_helpers import (
    attach_repository_contract_tests,
    run_repository_methods_test,
    run_repository_smoke_test,
)


class KeyProjectRepositoryTests(unittest.TestCase):
    def test_smoke_instantiation(self):
        run_repository_smoke_test(self, "KeyProjectRepository", "KeyProjectRepository")

    def test_methods_execute_with_fake_collection(self):
        run_repository_methods_test(self, "KeyProjectRepository", "KeyProjectRepository")

attach_repository_contract_tests(KeyProjectRepositoryTests, "KeyProjectRepository", "KeyProjectRepository")

if __name__ == "__main__":
    unittest.main()
