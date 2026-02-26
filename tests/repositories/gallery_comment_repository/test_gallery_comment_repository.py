import unittest

from tests.repositories.shared._repository_test_helpers import (
    attach_repository_contract_tests,
    run_repository_methods_test,
    run_repository_smoke_test,
)


class GalleryCommentRepositoryTests(unittest.TestCase):
    def test_smoke_instantiation(self):
        run_repository_smoke_test(self, "GalleryCommentRepository", "GalleryCommentRepository")

    def test_methods_execute_with_fake_collection(self):
        run_repository_methods_test(self, "GalleryCommentRepository", "GalleryCommentRepository")

attach_repository_contract_tests(GalleryCommentRepositoryTests, "GalleryCommentRepository", "GalleryCommentRepository")

if __name__ == "__main__":
    unittest.main()
