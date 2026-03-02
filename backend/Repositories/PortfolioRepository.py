from Repositories.BaseRepository import BaseRepository
from Repositories.Interfaces.IPortfolioRepository import IPortfolioRepository
from constants.db_collections import MongoCollections as mc

class PortfolioRepository(IPortfolioRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VISITORS)  # Call the constructor of the base class

    def insert_portfolio(self, portfolio_data):
        """Insert a portfolio document into the collection."""
        return self.collection.insert_one(portfolio_data)

    def insert_system_info(self, system_info):
        """Insert system information into a separate collection."""
        return self.collection.insert_one(system_info)
