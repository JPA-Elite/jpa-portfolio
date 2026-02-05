from backend.Repositories.BaseRepository import BaseRepository
from backend.Repositories.Interfaces.IPortfolioRepository import IPortfolioRepository
from backend.Models.Portfolio import Portfolio
from backend.Models.SystemInfo import SystemInfo
from backend.constants.db_collections import MongoCollections as mc


class PortfolioRepository(IPortfolioRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VISITORS)

    def insert_portfolio(self, portfolio_data: Portfolio):
        """Insert a portfolio model into the collection."""
        return self.insert_document(portfolio_data.to_dict())

    def insert_system_info(self, system_info: SystemInfo):
        """Insert a system-info model into the collection."""
        return self.insert_document(system_info.to_dict())
