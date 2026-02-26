import unittest

from tests.repositories.shared._repository_test_helpers import (
    attach_repository_contract_tests,
    run_repository_methods_test,
    run_repository_smoke_test,
)


class GalleryRepositoryTests(unittest.TestCase):
    def test_smoke_instantiation(self):
        run_repository_smoke_test(self, "GalleryRepository", "GalleryRepository")

    def test_methods_execute_with_fake_collection(self):
        run_repository_methods_test(self, "GalleryRepository", "GalleryRepository")

attach_repository_contract_tests(GalleryRepositoryTests, "GalleryRepository", "GalleryRepository")

if __name__ == "__main__":
    unittest.main()
