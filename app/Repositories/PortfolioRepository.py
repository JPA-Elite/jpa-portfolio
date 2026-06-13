from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IPortfolioRepository import IPortfolioRepository
from app.constants.db_collections import MongoCollections as mc

class PortfolioRepository(IPortfolioRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VISITORS)

    def insert_portfolio(self, portfolio_data):
        return self.collection.insert_one(portfolio_data)

    def insert_system_info(self, system_info):
        return self.collection.insert_one(system_info)

