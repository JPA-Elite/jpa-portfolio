from backend.Repositories.PortfolioRepository import PortfolioRepository


class _FakeCollection:
    def __init__(self):
        self.inserted = []

    def insert_one(self, payload):
        self.inserted.append(payload)
        return {"ok": 1}


class _FakeModel:
    def __init__(self, payload):
        self.payload = payload

    def to_dict(self):
        return self.payload



def test_insert_portfolio_uses_model_to_dict():
    repo = PortfolioRepository.__new__(PortfolioRepository)
    repo.collection = _FakeCollection()

    model = _FakeModel({"name": "Josh", "email": "a@b.com"})
    repo.insert_portfolio(model)

    assert repo.collection.inserted == [{"name": "Josh", "email": "a@b.com"}]



def test_insert_system_info_uses_model_to_dict():
    repo = PortfolioRepository.__new__(PortfolioRepository)
    repo.collection = _FakeCollection()

    model = _FakeModel({"system": "Linux", "os": "Ubuntu"})
    repo.insert_system_info(model)

    assert repo.collection.inserted == [{"system": "Linux", "os": "Ubuntu"}]
