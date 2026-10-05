class SeedService:
    @staticmethod
    def ensure_seeded(count_fn, seed_fn):
        if count_fn() > 0:
            return 0
        return seed_fn()
