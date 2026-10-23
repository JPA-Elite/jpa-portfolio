import unittest
from unittest.mock import MagicMock

from app.Services.SeedService import SeedService


class SeedServiceTests(unittest.TestCase):
    def test_ensure_seeded_skips_seed_when_records_exist(self):
        count_fn = MagicMock(return_value=1)
        seed_fn = MagicMock(return_value=5)

        result = SeedService.ensure_seeded(count_fn, seed_fn)

        self.assertEqual(result, 0)
        count_fn.assert_called_once_with()
        seed_fn.assert_not_called()

    def test_ensure_seeded_runs_seed_when_empty(self):
        count_fn = MagicMock(return_value=0)
        seed_fn = MagicMock(return_value=4)

        result = SeedService.ensure_seeded(count_fn, seed_fn)

        self.assertEqual(result, 4)
        count_fn.assert_called_once_with()
        seed_fn.assert_called_once_with()

    def test_ensure_seeded_returns_seed_result(self):
        seed_fn = MagicMock(return_value={"inserted": 2})

        result = SeedService.ensure_seeded(lambda: 0, seed_fn)

        self.assertEqual(result, {"inserted": 2})


if __name__ == "__main__":
    unittest.main()
