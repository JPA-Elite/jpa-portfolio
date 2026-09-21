from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IPortfolioRepository import IPortfolioRepository
from app.constants.db_collections import MongoCollections as mc

class PortfolioRepository(IPortfolioRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VISITORS)

    def insert_portfolio(self, portfolio_data):
        return self.insert_one(portfolio_data)

    def insert_system_info(self, system_info):
        return self.insert_one(system_info)

    def find_visit_for_day(self, ip_address, page, visit_date):
        return self.find_one({
            "ip_address": ip_address,
            "page": page,
            "visit_date": visit_date,
        })

